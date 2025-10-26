#include <Servo.h>

int motorSpeed;
Servo s1;

void setup() {
  Serial.begin(9600);  //initiate Serial communication
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  s1.attach(11);
}

void loop() 
{
  while (Serial.available() == 0)
  {}
  int iput = Serial.parseInt();
  Serial.println(iput);
  switch (iput)
  {
    case 1:
      motorSpeed = 120;
      Serial.println(motorSpeed);
      analogWrite(5, motorSpeed);
      analogWrite(6, motorSpeed);
      break;
    case 2:
      motorSpeed = 180;
      analogWrite(5, motorSpeed);
      analogWrite(6, motorSpeed);
      break;
    case 3:
      motorSpeed = 240;
      analogWrite(5, motorSpeed);
      analogWrite(6, motorSpeed);
      break;
    case 4://right
      analogWrite(5, 150);
      analogWrite(6, 50);
      break;
    case 5://left
      analogWrite(6, 150);
      analogWrite(5, 50);
      break;
    case 6://up
      s1.write(0);
      break;
    case 7://down
      s1.write(45);
      break;
    case 9:
      analogWrite(5, 0);
      analogWrite(6, 0);
      break;
  }//end switch
}