void setup() {
  Serial.begin(9600);
  analogReference(EXTERNAL);
}

void loop() {
    int sensorValueA0 = analogRead(A0); // Up
    int sensorValueA1 = analogRead(A1); // Down 
    int sensorValueA4 = analogRead(A4); // Left 
    int sensorValueA5 = analogRead(A5); // Right

    Serial.print(sensorValueA0);
    Serial.print(" ");

    Serial.print(sensorValueA1);
    Serial.print(" ");

    Serial.print(sensorValueA4);
    Serial.print(" ");

    Serial.print(sensorValueA5);
    Serial.println();  // This newline signals end-of-line for Python
    delay(50);
}
