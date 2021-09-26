/* exoems by romain and shan-yuan teng

   hardware:
   - 8 dc motors
   - 4 H-bridge L293D

*/
#define STUDY_SELECT A0 // 0: independence, 1: accuracy

#define BEND_SENSOR_1 A8
#define BEND_SENSOR_2 A9

const int I_PIP_EN  = 22;
const int I_PIP_CH1 = 23;
const int I_PIP_CH2 = 24;

const int I_MCP_EN  = 25;
const int I_MCP_CH1 = 26;
const int I_MCP_CH2 = 27;

const int M_PIP_EN  = 28;
const int M_PIP_CH1 = 29;
const int M_PIP_CH2 = 30;

const int M_MCP_EN  = 31;
const int M_MCP_CH1 = 32;
const int M_MCP_CH2 = 33;

const int R_PIP_EN  = 34;
const int R_PIP_CH1 = 35;
const int R_PIP_CH2 = 36;

const int R_MCP_EN  = 37;
const int R_MCP_CH1 = 38;
const int R_MCP_CH2 = 39;

const int P_PIP_EN  = 40;
const int P_PIP_CH1 = 41;
const int P_PIP_CH2 = 42;

const int P_MCP_EN  = 43;
const int P_MCP_CH1 = 44;
const int P_MCP_CH2 = 45;

unsigned long time;
unsigned long startTime;
unsigned long idleStartTime;

bool readButtons = true;

int currSwitch1 = 1;
int lastSwitch1 = 1;

int currSwitch2 = 1;
int lastSwitch2 = 1;

// Motor initial states, 0 = unlock, 1 = lock
int I_PIP_state = 0;
int I_MCP_state = 0;
int M_PIP_state = 0;
int M_MCP_state = 0;
int R_PIP_state = 0;
int R_MCP_state = 0;
int P_PIP_state = 0;
int P_MCP_state = 0;

void setup() {

  // Mode input
  pinMode(STUDY_SELECT , INPUT);

  //DEBUG
  pinMode(13, OUTPUT);
  
  pinMode(I_PIP_EN  , OUTPUT);
  pinMode(I_PIP_CH1 , OUTPUT);
  pinMode(I_PIP_CH2 , OUTPUT);

  pinMode(I_MCP_EN  , OUTPUT);
  pinMode(I_MCP_CH1 , OUTPUT);
  pinMode(I_MCP_CH2 , OUTPUT);
  
  pinMode(M_PIP_EN  , OUTPUT);
  pinMode(M_PIP_CH1 , OUTPUT);
  pinMode(M_PIP_CH2 , OUTPUT);

  pinMode(M_MCP_EN  , OUTPUT);
  pinMode(M_MCP_CH1 , OUTPUT);
  pinMode(M_MCP_CH2 , OUTPUT);
  
  pinMode(R_PIP_EN  , OUTPUT);
  pinMode(R_PIP_CH1 , OUTPUT);
  pinMode(R_PIP_CH2 , OUTPUT);

  pinMode(R_MCP_EN  , OUTPUT);
  pinMode(R_MCP_CH1 , OUTPUT);
  pinMode(R_MCP_CH2 , OUTPUT);
  
  pinMode(P_PIP_EN  , OUTPUT);
  pinMode(P_PIP_CH1 , OUTPUT);
  pinMode(P_PIP_CH2 , OUTPUT);

  pinMode(P_MCP_EN  , OUTPUT);
  pinMode(P_MCP_CH1 , OUTPUT);
  pinMode(P_MCP_CH2 , OUTPUT);

  Serial.begin(115200);
  Serial.setTimeout(2);

  // Disable all motors at start
  digitalWrite(I_PIP_EN, LOW);
  digitalWrite(I_MCP_EN, LOW);
  digitalWrite(M_PIP_EN, LOW);
  digitalWrite(M_MCP_EN, LOW);
  digitalWrite(R_PIP_EN, LOW);
  digitalWrite(R_MCP_EN, LOW);
  digitalWrite(P_PIP_EN, LOW);
  digitalWrite(P_MCP_EN, LOW);

//  Serial.println("USAGE");
//  Serial.println("-------------------------------------------------"); 
//  Serial.println("d1/d0: on and off led for debugging");
//  Serial.println("e0: disable all mux");
//  Serial.println("e1: enable all mux");
//  Serial.println("l0: unlock all motors");
//  Serial.println("l1: lock all motors");
//  Serial.println("u111: select index finger (1) MCP (1) to lock (1)");
//  Serial.println("-------------------------------------------------"); 
}

void loop() {
  /*----------- STUDY: independence ------------*/
  if(digitalRead(STUDY_SELECT) == LOW){
    // notes:
    // e0: disable all mux
    // e1: enable all mux
    // l0: unlock all motors
    // l1: lock all motors

//    Serial.println("Independence study: ");
    
    if (Serial.available()) {
      String incomingStr = Serial.readStringUntil('\n');
      // read two digits, e.g. "00", "11"
      String cmd1 = incomingStr.substring(0, 1);
      int cmd2 = incomingStr.substring(1, 2).toInt();
      int cmd3 = incomingStr.substring(2, 3).toInt();
      int cmd4 = incomingStr.substring(3, 4).toInt();
  
      Serial.println("Input: " + incomingStr);
  //    Serial.print(cmd1);
  //    Serial.print("\t");
  //    Serial.print(cmd2);
  //    Serial.print("\t");
  //    Serial.print(cmd3);
  //    Serial.print("\t");
  //    Serial.print(cmd4);
  //    Serial.println();
  
      // Disable motors
  
      // DEBUG: led
      if (cmd1 == "d"){
        if (cmd2 == 1) {
        digitalWrite(13, HIGH);
        } if (cmd2 == 0) {
          digitalWrite(13, LOW);
        }
      }
  
      if (cmd1 == "e"){
        enableAll(cmd2);
      }
  
      if (cmd1 == "l"){
        lockAll(cmd2);
      }
  
      if (cmd1 == "u"){
        switch (cmd2){ // finger selection
          case 1: // index
            // joint selection: 0-none, 1-MCP, 2-PIP, 3-both
            if (cmd3 == 0){
              I_MCP_state = 0;
              I_PIP_state = 0;
            }
            if (cmd3 == 1){
              I_MCP_state = cmd4;
            }
            if (cmd3 == 2){
              I_PIP_state = cmd4;
            }
            if (cmd3 == 3){
              I_MCP_state = 1;
              I_PIP_state = 1;
            }
            break;
          case 2: // middle
            // joint selection: 1-MCP, 2-PIP
            if (cmd3 == 0){
              M_MCP_state = 0;
              M_PIP_state = 0;
            }
            if (cmd3 == 1){
              M_MCP_state = cmd4;
            }
            if (cmd3 == 2){
              M_PIP_state = cmd4;
            }
            if (cmd3 == 3){
              M_MCP_state = 1;
              M_PIP_state = 1;
            }
            break;
          case 3: // ring
            // joint selection: 1-MCP, 2-PIP
            if (cmd3 == 0){
              R_MCP_state = 0;
              R_PIP_state = 0;
            }
            if (cmd3 == 1){
              R_MCP_state = cmd4;
            }
            if (cmd3 == 2){
              R_PIP_state = cmd4;
            }
            if (cmd3 == 3){
              R_MCP_state = 1;
              R_PIP_state = 1;
            }
            break;
          case 4: // pinky 
           // joint selection: 1-MCP, 2-PIP
            if (cmd3 == 0){
              P_MCP_state = 0;
              P_PIP_state = 0;
            }
            if (cmd3 == 1){
              P_MCP_state = cmd4;
            }
            if (cmd3 == 2){
              P_PIP_state = cmd4;
            }
            if (cmd3 == 3){
              P_MCP_state = 1;
              P_PIP_state = 1;
            }
            break;
          default:
            //Serial.println("Wrong input");
            break;
        }
      }
  //    // Unlock individual
  //    if (incomingStr == "1") { // index PIP
  //      I_PIP_state = 0;
  //    }
  //    if (incomingStr == "2") { // index MCP
  //      I_MCP_state = 0;
  //    }
  //    if (incomingStr == "3") { // middle PIP
  //      M_PIP_state = 0;
  //    }
  //    if (incomingStr == "4") { // middle MCP
  //      M_MCP_state = 0;
  //    }
  //    if (incomingStr == "5") { // ring PIP
  //      R_PIP_state = 0;
  //    }
  //    if (incomingStr == "6") { // ring MCP
  //      R_MCP_state = 0;
  //    }
  //    if (incomingStr == "7") { // pinky PIP
  //      P_PIP_state = 0;
  //    }
  //    if (incomingStr == "8") { // pinky MCP
  //      P_MCP_state = 0;
  //    }
  //    
  //    idleStartTime = millis();
  //    digitalWrite(I_PIP_EN, HIGH);
  //    digitalWrite(I_MCP_EN, HIGH);
  //    digitalWrite(M_PIP_EN, HIGH);
  //    digitalWrite(M_MCP_EN, HIGH);
  //    digitalWrite(R_PIP_EN, HIGH);
  //    digitalWrite(R_MCP_EN, HIGH);
  //    digitalWrite(P_PIP_EN, HIGH);
  //    digitalWrite(P_MCP_EN, HIGH);
    }
  
  //  // turn off motors after 2 secs to prevent over heating
  //  if (millis() - idleStartTime > 2000) {
  //    digitalWrite(I_PIP_EN, LOW);
  //    digitalWrite(I_MCP_EN, LOW);
  //    digitalWrite(M_PIP_EN, LOW);
  //    digitalWrite(M_MCP_EN, LOW);
  //    digitalWrite(R_PIP_EN, LOW);
  //    digitalWrite(R_MCP_EN, LOW);
  //    digitalWrite(P_PIP_EN, LOW);
  //    digitalWrite(P_MCP_EN, LOW);
  //  }
  
    // Index PIP motor drive
    if (I_PIP_state == 1) {
      digitalWrite(I_PIP_CH1, LOW);
      digitalWrite(I_PIP_CH2, HIGH);
    } else if (I_PIP_state == 0) {
      digitalWrite(I_PIP_CH1, HIGH);
      digitalWrite(I_PIP_CH2, LOW);
    }
    // Index MCP motor drive
    if (I_MCP_state == 1) {
      digitalWrite(I_MCP_CH1, LOW);
      digitalWrite(I_MCP_CH2, HIGH);
    } else if (I_MCP_state == 0) {
      digitalWrite(I_MCP_CH1, HIGH);
      digitalWrite(I_MCP_CH2, LOW);
    }
  
    if (M_PIP_state == 1) {
      digitalWrite(M_PIP_CH1, LOW);
      digitalWrite(M_PIP_CH2, HIGH);
    } else if (M_PIP_state == 0) {
      digitalWrite(M_PIP_CH1, HIGH);
      digitalWrite(M_PIP_CH2, LOW);
    }
  
    if (M_MCP_state == 0) { // wires inverted
      digitalWrite(M_MCP_CH1, LOW);
      digitalWrite(M_MCP_CH2, HIGH);
    } else if (M_MCP_state == 1) {
      digitalWrite(M_MCP_CH1, HIGH);
      digitalWrite(M_MCP_CH2, LOW);
    }
  
    if (R_PIP_state == 0) { // wires inverted
      digitalWrite(R_PIP_CH1, LOW);
      digitalWrite(R_PIP_CH2, HIGH);
    } else if (R_PIP_state == 1) {
      digitalWrite(R_PIP_CH1, HIGH);
      digitalWrite(R_PIP_CH2, LOW);
    }
  
    if (R_MCP_state == 0) { // wires inverted
      digitalWrite(R_MCP_CH1, LOW);
      digitalWrite(R_MCP_CH2, HIGH);
    } else if (R_MCP_state == 1) {
      digitalWrite(R_MCP_CH1, HIGH);
      digitalWrite(R_MCP_CH2, LOW);
    }
  
    if (P_PIP_state == 1) {
      digitalWrite(P_PIP_CH1, LOW);
      digitalWrite(P_PIP_CH2, HIGH);
    } else if (P_PIP_state == 0) {
      digitalWrite(P_PIP_CH1, HIGH);
      digitalWrite(P_PIP_CH2, LOW);
    }
  
    if (P_MCP_state == 1) {
      digitalWrite(P_MCP_CH1, LOW);
      digitalWrite(P_MCP_CH2, HIGH);
    } else if (P_MCP_state == 0) {
      digitalWrite(P_MCP_CH1, HIGH);
      digitalWrite(P_MCP_CH2, LOW);
    }
  
    delay(10);
    }
    
  /*----------- STUDY: accuracy ------------*/
  else{
//    Serial.println("Accuracy study: ");
    // Receive exo command
    if (Serial.available()) {
      String incomingStr = Serial.readStringUntil('\n');
      // read two digits, e.g. "00", "11"
      int cmd1 = incomingStr.substring(0, 1).toInt();
      R_MCP_state = cmd1;
    }

    // disabling non-essential motors
    digitalWrite(I_PIP_EN, LOW);
    digitalWrite(I_MCP_EN, LOW);
    digitalWrite(M_PIP_EN, LOW);
    digitalWrite(M_MCP_EN, LOW);
    digitalWrite(R_PIP_EN, LOW);
    digitalWrite(R_MCP_EN, HIGH);
    digitalWrite(P_PIP_EN, LOW);
    digitalWrite(P_MCP_EN, LOW);
    
    if (R_MCP_state == 0) { // wires inverted
      digitalWrite(R_MCP_CH1, LOW);
      digitalWrite(R_MCP_CH2, HIGH);
    } else if (R_MCP_state == 1) {
      digitalWrite(R_MCP_CH1, HIGH);
      digitalWrite(R_MCP_CH2, LOW);
    }
    
    // Send bend sensor
//    int bend_avg = (int) ( ( analogRead(BEND_SENSOR_1) + analogRead(BEND_SENSOR_1)) / 2);
//    Serial.println(bend_avg);
//    Serial.flush();
    delay(10);
  }
}

void enableAll(int enable){
  digitalWrite(I_PIP_EN, enable);
  digitalWrite(I_MCP_EN, enable);
  digitalWrite(M_PIP_EN, enable);
  digitalWrite(M_MCP_EN, enable);
  digitalWrite(R_PIP_EN, enable);
  digitalWrite(R_MCP_EN, enable);
  digitalWrite(P_PIP_EN, enable);
  digitalWrite(P_MCP_EN, enable);

  //Serial.println("enable: " + enable);
}

void lockAll(int state){
  I_PIP_state = state;
  I_MCP_state = state;
  M_PIP_state = state;
  M_MCP_state = state;
  R_PIP_state = state;
  R_MCP_state = state;
  P_PIP_state = state;
  P_MCP_state = state;

  //Serial.println("state: " + state);
}
