int const flex1 = A0; // Up 
int const flex2 = A1; // Down
int const flex3 = A4; // Left
int const flex4 = A5; // Right
int flexVal1;
int flexVal2;  
int flexVal3;  
int flexVal4;  


void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
flexVal1 = analogRead(flex1);
flexVal2 = analogRead(flex2);
flexVal3 = analogRead(flex3);
flexVal4 = analogRead(flex4);

Serial.print("flexVal1: ");
Serial.print(flexVal1);

Serial.print(" ");

Serial.print("flexVal2: ");
Serial.print(flexVal2);

Serial.print(" ");

Serial.print("flexVal3: ");
Serial.print(flexVal3);

Serial.print(" ");

Serial.print("flexVal4: ");
Serial.println(flexVal4);
}