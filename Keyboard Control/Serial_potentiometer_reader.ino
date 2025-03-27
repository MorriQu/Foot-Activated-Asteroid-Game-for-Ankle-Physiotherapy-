int const potPin = A0;
int potVal; 


void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
potVal = analogRead(potPin);

Serial.print("potVal: ");
Serial.println(potVal);
}
