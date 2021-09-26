// Pinout - add thumb if available
// Thumb
const int T_PIP_EN;
const int T_PIP_CH1;
const int T_PIP_CH2;

const int T_MCP_EN;
const int T_MCP_CH1;
const int T_MCP_CH2;
// Index
const int I_PIP_EN  = 22;
const int I_PIP_CH1 = 23;
const int I_PIP_CH2 = 24;

const int I_MCP_EN  = 25;
const int I_MCP_CH1 = 26;
const int I_MCP_CH2 = 27;
// Middle
const int M_PIP_EN  = 28;
const int M_PIP_CH1 = 29;
const int M_PIP_CH2 = 30;

const int M_MCP_EN  = 31;
const int M_MCP_CH1 = 32;
const int M_MCP_CH2 = 33;
// Ring
const int R_PIP_EN  = 34;
const int R_PIP_CH1 = 35;
const int R_PIP_CH2 = 36;

const int R_MCP_EN  = 37;
const int R_MCP_CH1 = 38;
const int R_MCP_CH2 = 39;
// Pinky
const int P_PIP_EN  = 40;
const int P_PIP_CH1 = 41;
const int P_PIP_CH2 = 42;

const int P_MCP_EN  = 43;
const int P_MCP_CH1 = 44;
const int P_MCP_CH2 = 45;

// stores the motor states
uint8_t motor_state[10];
uint8_t motor_state_prev[10]; // stores previous state, preventing them to get updated everytime

// stores the motor pins
// note some channels are flipped (2 before 1) because they are wired in reverse on demo exo
uint8_t motor_arr[20] = {T_MCP_CH1, T_MCP_CH2, T_PIP_CH1, T_PIP_CH2,
                     I_MCP_CH1, I_MCP_CH2, I_PIP_CH1, I_PIP_CH2,
                     M_MCP_CH2, M_MCP_CH1, M_PIP_CH1, M_PIP_CH2,
                     R_MCP_CH2, R_MCP_CH1, R_PIP_CH2, R_PIP_CH1,
                     P_MCP_CH1, P_MCP_CH2, P_PIP_CH1, P_PIP_CH2};

// Serial communication
const byte buffSize = 40;
byte inputBuffer[buffSize];

// Set this to true if exo has thumb
bool thumb = false;

void setup() {
  if (thumb){
    pinMode(T_PIP_EN  , OUTPUT);
    pinMode(T_PIP_CH1 , OUTPUT);
    pinMode(I_PIP_CH2 , OUTPUT);
  
    pinMode(T_MCP_EN  , OUTPUT);
    pinMode(T_MCP_CH1 , OUTPUT);
    pinMode(T_MCP_CH2 , OUTPUT);
  }
  
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
  
  Serial.begin(9600);
  Serial.setTimeout(2);

  // Disable all motors at start
  if (thumb){
    digitalWrite(T_PIP_EN, LOW);
    digitalWrite(T_MCP_EN, LOW);  
  }
  digitalWrite(I_PIP_EN, LOW);
  digitalWrite(I_MCP_EN, LOW);
  digitalWrite(M_PIP_EN, LOW);
  digitalWrite(M_MCP_EN, LOW);
  digitalWrite(R_PIP_EN, LOW);
  digitalWrite(R_MCP_EN, LOW);
  digitalWrite(P_PIP_EN, LOW);
  digitalWrite(P_MCP_EN, LOW);
}

void loop() {
  if (Serial.available()) 
  {
    Serial.readBytes(inputBuffer, 2); // wait for 2 bytes in buffer
    
    // MSB data
    motor_state[0] = ((inputBuffer[0]>>1)&1);
    motor_state[1] = ((inputBuffer[0]>>0)&1);
    
    // LSB data
    motor_state[2] = ((inputBuffer[1]>>7)&1);
    motor_state[3] = ((inputBuffer[1]>>6)&1);
    motor_state[4] = ((inputBuffer[1]>>5)&1);
    motor_state[5] = ((inputBuffer[1]>>4)&1);
    motor_state[6] = ((inputBuffer[1]>>3)&1);
    motor_state[7] = ((inputBuffer[1]>>2)&1);
    motor_state[8] = ((inputBuffer[1]>>1)&1);
    motor_state[9] = ((inputBuffer[1]>>0)&1);

    updateMotors();
    printMotors();
  }
}

void printMotors(){
  Serial.print("Motors in binary: ");
  for (int i = 0; i < sizeof(motor_state); i++){
      Serial.print(motor_state[i]);
    }
  Serial.println("");
}

void updateMotors(){
  for (int i = 0; i < sizeof(motor_state); ++i)
  {
      if (motor_state[i] == 1 && motor_state [i] != motor_state_prev[i])       // lock motor
      {
          lock_motor(i);
          motor_state_prev[i] = motor_state[i];
      }
      else if (motor_state[i] == 0 && motor_state [i] != motor_state_prev[i])  // unlock motor
      {
          unlock_motor(i);
          motor_state_prev[i] = motor_state[i];
      }
  }
}

void lock_motor(int index){
  digitalWrite(motor_arr[index * 2], LOW);
  digitalWrite(motor_arr[index * 2 + 1], HIGH);
  Serial.println("Locking motor " + index);
}

void unlock_motor(int index){
  digitalWrite(motor_arr[index * 2], LOW);
  digitalWrite(motor_arr[index * 2 + 1], HIGH);
  Serial.println("Unlocking motor " + index);
}

void enableMotors(int enable){
  if (thumb){
    digitalWrite(T_PIP_EN, enable);
    digitalWrite(T_MCP_EN, enable);  
  }
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
