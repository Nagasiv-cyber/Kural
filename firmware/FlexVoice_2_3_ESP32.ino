// FlexVoice 2.3: FLEX GPIO32, POT wiper GPIO34, MPU6050 SDA21 SCL22.
// Pot outer pins to 3.3V and GND. Disconnect USB before rewiring.
// Output: flex,pot,ax,ay,az,gx,gy,gz,OK (115200 baud)
#include <Wire.h>
#define FLEX_PIN 32
#define POT_PIN 34
#define MPU_ADDR 0x68
bool ready=false;
bool writeMPU(uint8_t reg,uint8_t val){Wire.beginTransmission(MPU_ADDR);Wire.write(reg);Wire.write(val);return Wire.endTransmission()==0;}
void setup(){Serial.begin(115200);analogReadResolution(12);analogSetPinAttenuation(FLEX_PIN,ADC_11db);analogSetPinAttenuation(POT_PIN,ADC_11db);Wire.begin(21,22);Wire.setClock(100000);delay(700);ready=writeMPU(0x6B,0)&&writeMPU(0x1C,0)&&writeMPU(0x1B,0);}
void loop(){
 if(!ready){Serial.println("MPU6050_NOT_FOUND");delay(500);ready=writeMPU(0x6B,0)&&writeMPU(0x1C,0)&&writeMPU(0x1B,0);return;}
 int flex=analogRead(FLEX_PIN),pot=analogRead(POT_PIN);
 Wire.beginTransmission(MPU_ADDR);Wire.write(0x3B);
 if(Wire.endTransmission(false)!=0||Wire.requestFrom(MPU_ADDR,14,true)!=14){delay(50);return;}
 int16_t ax=(Wire.read()<<8)|Wire.read(),ay=(Wire.read()<<8)|Wire.read(),az=(Wire.read()<<8)|Wire.read();
 Wire.read();Wire.read();
 int16_t gx=(Wire.read()<<8)|Wire.read(),gy=(Wire.read()<<8)|Wire.read(),gz=(Wire.read()<<8)|Wire.read();
 Serial.print(flex);Serial.print(',');Serial.print(pot);Serial.print(',');
 Serial.print(ax/16384.0,3);Serial.print(',');Serial.print(ay/16384.0,3);Serial.print(',');Serial.print(az/16384.0,3);Serial.print(',');
 Serial.print(gx/131.0,2);Serial.print(',');Serial.print(gy/131.0,2);Serial.print(',');Serial.print(gz/131.0,2);Serial.print(',');
 Serial.println((flex<=0||flex>=4095||pot<0||pot>=4095)?"CHECK_ADC":"OK");
 delay(40);
}