
import argparse
import time
import collections

import pandas as pd
import joblib

from common import *
from speech_windows import VoiceWorker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM7")
    parser.add_argument("--name", default="Visagan")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--confidence", type=float, default=0.50)
    args = parser.parse_args()

    # Load trained ML model
    payload = joblib.load(ROOT / "phrase_model_v23.joblib")

    if payload.get("version") != "2.3":
        raise SystemExit("Wrong model version")

    model = payload["model"]
    features = payload["features"]

    speaker = VoiceWorker()

    # Faster gesture recognition
    window = collections.deque(maxlen=3)

    armed = True
    rest_count = 0
    last_said = 0
    last_debug = 0
    last_warning = 0

    print("\nFlexVoice 2.3 LIVE started!")
    print("Fast recognition enabled.")
    print("Return both sensors to REST between phrases.")
    print("Press Ctrl+C to stop.\n")

    try:
        with serial_open(args.port) as ser:
            time.sleep(1.5)
            ser.reset_input_buffer()

            while True:
                raw = ser.readline().decode(
                    "utf-8", errors="replace"
                )

                row = parse(raw)

                if row is None:
                    continue

                flex = row["flex"]
                pot = row["pot"]
                now = time.monotonic()

                # Reject invalid potentiometer readings
                if pot == 0:
                    window.clear()
                    rest_count = 0

                    if args.debug and now - last_warning >= 1.0:
                        print(
                            "WARNING: POT=0 - check GPIO34 wiring",
                            flush=True
                        )
                        last_warning = now

                    continue

                # Detect REST and unlock next gesture
                if flex <= 235 and pot <= 1400:
                    rest_count += 1
                    window.clear()

                    if rest_count >= 3:
                        if not armed:
                            print(
                                "\nREADY: Next gesture enabled\n",
                                flush=True
                            )
                        armed = True

                    if args.debug and now - last_debug >= 0.5:
                        print(
                            f"REST | FLEX={flex:.0f} "
                            f"POT={pot:.0f} "
                            f"ARMED={armed}",
                            flush=True
                        )
                        last_debug = now

                    continue

                rest_count = 0

                # Determine activated sensor
                if flex >= 245 and pot <= 1400:
                    kind = "FLEX"

                elif flex <= 235 and pot >= 2400:
                    kind = "POT"

                else:
                    window.clear()

                    if args.debug and now - last_debug >= 0.5:
                        print(
                            f"WAIT | FLEX={flex:.0f} "
                            f"POT={pot:.0f} "
                            f"Outside gesture ranges",
                            flush=True
                        )
                        last_debug = now

                    continue

                # Match model feature names and order
                X = pd.DataFrame(
                    [[row[k] for k in features]],
                    columns=features
                )

                probabilities = model.predict_proba(X)[0]
                index = int(probabilities.argmax())

                label = model.classes_[index]
                confidence = float(probabilities[index])

                correct_kind = KIND.get(label) == kind

                accepted = (
                    correct_kind
                    and confidence >= args.confidence
                )

                # Show predictions
                if args.debug and now - last_debug >= 0.5:
                    print(
                        f"PRED={label:13} "
                        f"CONF={confidence:.0%} "
                        f"FLEX={flex:.0f} "
                        f"POT={pot:.0f} "
                        f"EXPECTED={kind} "
                        f"ARMED={armed} "
                        f"ACCEPTED={accepted}",
                        flush=True
                    )
                    last_debug = now

                # Do not collect votes while locked
                if not armed:
                    window.clear()
                    continue

                if not accepted:
                    window.clear()
                    continue

                # Collect recent matching predictions
                window.append(label)

                # Faster speech trigger
                if (
                    len(window) == 3
                    and window.count(label) >= 2
                    and now - last_said > 1.2
                ):
                    phrase = PHRASES[label].format(
                        name=args.name
                    )

                    print(
                        f"\nSPEAK: {phrase}\n",
                        flush=True
                    )

                    speaker.say(phrase)

                    # Lock until REST is detected
                    armed = False
                    last_said = now
                    window.clear()

    except KeyboardInterrupt:
        print("\nFlexVoice stopped.")

    finally:
        speaker.stop()


if __name__ == "__main__":
    main()