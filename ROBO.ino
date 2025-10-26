#include <Servo.h>

int motorSpeed;
Servo s1;

void setup() {
  Serial.begin(9600);  //initiate Serial communication
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  s1.attach(11);
  s1.write(180);
}

void loop() 
{
  while (Serial.available() == 0)
  {}
  int iput = Serial.parseInt();
  switch (iput)
  {
    case 1:
      s1.write(180);
      motorSpeed = 120;
      analogWrite(5, motorSpeed);
      analogWrite(6, motorSpeed);
      Serial.println("Done1");
      break;
    case 2:
      s1.write(180);
      motorSpeed = 180;
      analogWrite(5, motorSpeed);
      analogWrite(6, motorSpeed);
      Serial.println("Done2");
      break;
    case 3:
      s1.write(180);
      motorSpeed = 240;
      analogWrite(5, motorSpeed);
      analogWrite(6, motorSpeed);
      Serial.println("Done3");
      break;
    case 4://right
      analogWrite(5, 120);
      analogWrite(6, 0);
      s1.write(135);
      Serial.println("Done4");
      break;
    case 5://left
      analogWrite(6, 120);
      analogWrite(5, 0);
      s1.write(135);
      Serial.println("Done5");
      break;
    case 9:
      s1.write(180);
      analogWrite(5, 0);
      analogWrite(6, 0);
      Serial.println("Done9");
      break;
  }//end switch
}
