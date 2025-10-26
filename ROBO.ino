#include <Servo.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

int motorSpeed;
int iput;
float zoffset;
unsigned long lastTime = 0; 
Servo s1;
Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  s1.attach(11);
  s1.write(180);
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  lastTime = micros();
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  zoffset = g.gyro.z;
}

void loop() 
{
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  float angleZ = 0.0f;     
  lastTime = 0; 

  // Print the turn rate (angular velocity) data
  Serial.print("Turn Rate (rad/s) X: ");
  Serial.print(g.gyro.x);
  Serial.print(", Y: ");
  Serial.print(g.gyro.y);
  Serial.print(", Z: ");
  Serial.println(g.gyro.z - zoffset);

  delay(500);
  clearInputBuffer();
  while (Serial.available() == 0)
  {}
  iput = Serial.parseInt();
  Serial.println(iput);
  if (iput == 1)
  {
    clearInputBuffer();
    s1.write(180);
    motorSpeed = 120;
    analogWrite(5, motorSpeed);
    analogWrite(6, motorSpeed);
    Serial.println("Done1");
  }
  else if (iput == 2)
  {
    clearInputBuffer();
    s1.write(180);
    motorSpeed = 180;
    analogWrite(5, motorSpeed);
    analogWrite(6, motorSpeed);
    Serial.println("Done2");
  }
  else if (iput == 3)
  {
    clearInputBuffer();
    s1.write(180);
    motorSpeed = 240;
    analogWrite(5, motorSpeed);
    analogWrite(6, motorSpeed);
    Serial.println("Done3");
  }
  else if (iput == 4)
  {
    clearInputBuffer();
    while (Serial.available() == 0){}
    float turnAngleR = Serial.parseInt();
    Serial.println(angleZ);
    Serial.println(turnAngleR);
    analogWrite(5, 180);
    analogWrite(6, 50);
    s1.write(125);
    while (angleZ < turnAngleR)
    {
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      unsigned long now = micros();
      float dt = (now - lastTime) / 1000000.0f;  // dt in seconds
      lastTime = now;
      float gyroZ_rate = ((g.gyro.z - zoffset) * (180/M_PI));  // deg/s
      angleZ += abs(gyroZ_rate * dt);
      Serial.println(angleZ);
    }
    s1.write(180);
    analogWrite(5, 0);
    analogWrite(6, 0);
    Serial.println("Done4");
  }
  else if (iput == 5)
  {
    clearInputBuffer();
    while (Serial.available() == 0){}
    float turnAngleL = Serial.parseInt();
    Serial.println(turnAngleL);
    analogWrite(6, 180);
    analogWrite(5, 0);
    s1.write(125);
    while (angleZ <= turnAngleL)
    {
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      unsigned long now = micros();
      float dt = (now - lastTime) / 1000000.0f;  // dt in seconds
      lastTime = now;
      float gyroZ_rate = ((g.gyro.z - zoffset) * (180/M_PI));  // deg/s
      angleZ += abs(gyroZ_rate * dt);
    }
    s1.write(180);
    analogWrite(6, 0);
    analogWrite(5, 0);
    Serial.println("Done5");
  }
  else if (iput == 9)
  {
    clearInputBuffer();
    analogWrite(5, 0);
    analogWrite(6, 0);
    Serial.println("Done9");
  }
}


void clearInputBuffer() {
  while (Serial.available()) {
    Serial.read(); 
  }
}
