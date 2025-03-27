int upSwitchState = 0; 
int downSwitchState = 0; 


void setup() {
  // put your setup code here, to run once:
  pinMode(3, OUTPUT); // Red LED
  pinMode(4, OUTPUT); // Green LED
  pinMode(5, OUTPUT); // Green LED
  pinMode(2, INPUT); // Up button
  pinMode(6, INPUT); // Down button
  
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  upSwitchState = digitalRead(6); 
  downSwitchState = digitalRead(2);

  
  Serial.print("upSwitchState: ");
  Serial.print(upSwitchState);
  Serial.print("\t");

  Serial.print("downSwitchState: ");
  Serial.println(downSwitchState);
  
  if (upSwitchState == LOW && downSwitchState == LOW) {
    digitalWrite(3, LOW); //  
    digitalWrite(4, LOW); 
    digitalWrite(5, LOW);
  }

  if (upSwitchState == LOW && downSwitchState == HIGH) {
    digitalWrite(3, HIGH); // Flashing red light
    delay(100);
    digitalWrite(3, LOW);
    delay(100); 
  }

if (upSwitchState == HIGH && downSwitchState == LOW) {
    digitalWrite(4, HIGH); // Flashing green light
    delay(100);
    digitalWrite(4, LOW);
    delay(100); 
  }
 
 delay(200);

}
