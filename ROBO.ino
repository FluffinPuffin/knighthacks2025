#include <Servo.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

int motorSpeed;
int iput;
float zoffset;
float xoffset, yoffset;
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
  Serial.println("MPU6050 Found");
  mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  delay(300);
  lastTime = micros();
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  zoffset = g.gyro.z;
  xoffset = a.acceleration.x;
  yoffset = a.acceleration.y;
}

void loop() 
{
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  float angleZ = 0.0f;
  float position = 0.0f;
  int counter = 0;
  /*
  Serial.print("Acceleration: " );
  Serial.println(a.acceleration.x - xoffset);
  Serial.println(a.acceleration.y - yoffset);
  Serial.print("Turn rate: ");
  Serial.println(g.gyro.z - zoffset);
  */
  delay(200);
  clearInputBuffer();
  while (Serial.available() == 0)
  {}
  iput = Serial.parseInt();
  Serial.println(iput);
  if (iput == 1)
  {
    clearInputBuffer();
    while (Serial.available() == 0){}
    float distance = Serial.parseFloat();
    s1.write(180);
    //Serial.println(position);
    motorSpeed = 120;
    analogWrite(5, motorSpeed);
    analogWrite(6, motorSpeed);
    while (position < distance)
    {
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      unsigned long now = micros();
      if (counter == 0)
      {
        counter++;
        lastTime = now;
      }
      float dt = (now - lastTime) / 1000000.0f; 
      lastTime = now;
      //Serial.println(dt);
      float accelX_rate = sqrt(pow((a.acceleration.x - xoffset), 2) + pow((a.acceleration.y - yoffset), 2));
      position += abs(accelX_rate * (dt*dt));
      //Serial.println(position);
    }
    analogWrite(5, 0);
    analogWrite(6, 0);
    Serial.println("Done1");
  }
  else if (iput == 2)
  {
    clearInputBuffer();
    while (Serial.available() == 0){}
    float distance = Serial.parseFloat();
    s1.write(180);
    motorSpeed = 180;
    analogWrite(5, motorSpeed);
    analogWrite(6, motorSpeed);
    while (position < distance)
    {
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      unsigned long now = micros();
      if (counter == 0)
      {
        counter++;
        lastTime = now;
      }
      float dt = (now - lastTime) / 1000000.0f; 
      lastTime = now;
      //Serial.println(dt);
      float accelX_rate = sqrt(pow((a.acceleration.x - xoffset), 2) + pow((a.acceleration.y - yoffset), 2));
      position += abs(accelX_rate * (dt*dt));
      //Serial.println(position);
    }
    analogWrite(5, 0);
    analogWrite(6, 0);
    Serial.println("Done2");
  }
  else if (iput == 3)
  {
    clearInputBuffer();
    while (Serial.available() == 0){}
    float distance = Serial.parseFloat();
    s1.write(180);
    motorSpeed = 240;
    analogWrite(5, motorSpeed);
    analogWrite(6, motorSpeed);
    while (position < distance)
    {
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      unsigned long now = micros();
      if (counter == 0)
      {
        counter++;
        lastTime = now;
      }
      float dt = (now - lastTime) / 1000000.0f; 
      lastTime = now;
      //Serial.println(dt);
      float accelX_rate = sqrt(pow((a.acceleration.x - xoffset), 2) + pow((a.acceleration.y - yoffset), 2));
      position += abs(accelX_rate * (dt*dt));
      //Serial.println(position);
    }
    analogWrite(5, 0);
    analogWrite(6, 0);
    Serial.println("Done3");
  }
  else if (iput == 4)
  {
    clearInputBuffer();
    while (Serial.available() == 0){}
    float turnAngleR = Serial.parseInt();
    //Serial.println(angleZ);
    //Serial.println(turnAngleR);
    analogWrite(5, 240);
    analogWrite(6, 0);
    s1.write(115);
    while (angleZ <= turnAngleR)
    {
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      unsigned long now = micros();
      float dt = (now - lastTime) / 1000000.0f; 
      lastTime = now;
      float gyroZ_rate = ((g.gyro.z - zoffset) * (180/M_PI));  // deg/s
      angleZ += abs(gyroZ_rate * dt);
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
    //Serial.println(turnAngleL);
    analogWrite(6, 240);
    analogWrite(5, 0);
    s1.write(115);
    while (angleZ <= turnAngleL)
    {
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);
      unsigned long now = micros();
      float dt = (now - lastTime) / 1000000.0f;  
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

