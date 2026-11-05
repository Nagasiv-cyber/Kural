"""Non-blocking, serialized Windows SAPI speech with PowerShell fallback."""
from queue import Queue, Full
from threading import Thread
import subprocess
import base64


def fallback_speak(text):
    # Windows native System.Speech: separate process avoids COM state problems.
    escaped = text.replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Speech; "
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"try {{$s.Speak('{escaped}')}} finally {{$s.Dispose()}}"
    )
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    try:
        completed = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
            capture_output=True, text=True, timeout=25,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if completed.returncode:
            print('Speech error:', (completed.stderr or completed.stdout).strip())
    except Exception as exc:
        print('Speech error:', exc)


class VoiceWorker:
    """SAPI is created on the worker's own COM-initialized thread."""
    def __init__(self):
        self.queue = Queue(maxsize=3)
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()

    def say(self, sentence):
        try:
            self.queue.put_nowait(str(sentence))
        except Full:
            print('Speech queue full; skipped duplicate gesture.')

    def _run(self):
        com_ready = False
        voice = None
        pythoncom = None
        try:
            import pythoncom as _pythoncom
            import win32com.client
            pythoncom = _pythoncom
            pythoncom.CoInitialize()
            com_ready = True
            voice = win32com.client.Dispatch('SAPI.SpVoice')
            voice.Rate = -1
            voice.Volume = 100
        except Exception as exc:
            print('SAPI fallback:', exc)
        try:
            while True:
                sentence = self.queue.get()
                try:
                    if sentence is None:
                        return
                    if voice is not None:
                        try:
                            voice.Speak(sentence)
                        except Exception as exc:
                            print('SAPI retry using Windows speech:', exc)
                            fallback_speak(sentence)
                    else:
                        fallback_speak(sentence)
                finally:
                    self.queue.task_done()
        finally:
            voice = None
            if com_ready:
                pythoncom.CoUninitialize()

    def stop(self):
        self.queue.put(None)
        self.thread.join(timeout=30)