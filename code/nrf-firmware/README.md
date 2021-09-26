# Firmware for nRF52811

## Getting started

dextrEMS' nRF firmware is built from Nordic Semiconductor's nRF5 SDK 16.0.0 (https://www.nordicsemi.com/Products/Development-software/nRF5-SDK/Download#infotabs), based on the *ble_app_blinky* example. 

This current firmware was compiled with Segger Embedded Studio (https://www.segger.com/products/development-tools/embedded-studio/) using a 6-pin target Tag-Connect cable (https://www.tag-connect.com/product/tc2030-pkt-icespi-nl) and J-Link EDU Mini (https://www.segger.com/products/debug-probes/j-link/models/j-link-edu-mini/)

### How to install folder

Download the SDK 16.0.0 from Nordic Semiconductor's website.

In the root folder of the SDK, create a new folder called *projects*

Place the *dextrEMS* project folder in the *projects* 

Since we are using the nRF52811microcontroller with Segger Embedded Studio (SES), open the project with `projects/dextrEMS/ble_app_blinky/pca10056e/s112/ses/ble_app_blinky_pca10056e_s112.emProject`

## nRF code wiki

### How motors work

There are 3 arrays describing the motors:

- `static uint8_t motors[10]` : describes the **motor state** where 1 is locked and 0 is unlocked
- `static uint8_t motors_prev[10]` : describes the **previous motor state** which should prevent needing to update motors every time
- `static uint8_t motor_arr[20]` : describes the **motor pin** physical assignment which are defined by the following list:

```c
#define M1_1 25
#define M1_2 26
#define M2_1 27
#define M2_2 28
#define M3_1 21
#define M3_2 20
#define M4_1 19
#define M4_2 18
#define M6_1 17
#define M6_2 16
#define M5_1 15
#define M5_2 14
#define M8_1 13
#define M8_2 12
#define M7_1 11
#define M7_2 10
#define M9_1 9
#define M9_2 8
#define M10_1 7
#define M10_2 6
```

### Functions description

#### Motor functions

**The current version constantly drives the motors as the timing for locking/unlocking is not clear. Please check if the motors are running hot and turn off the motors accordingly. To test the code, please first use the LEDs to check the logic.**

```c
static void motor_init(void)
{
    uint32_t i;
    for (i = 0; i < MOTOR_NUMBER; ++i)
    {
        nrf_gpio_cfg_output(motor_arr[i]);
    }

    // init DEBUG_LED
    nrf_gpio_cfg_output(DEBUG_LED);
}
```

motor_init cycles through all the elements in motor_arr[] and set them as output. The motor pins are stored in the motor_arr[] and can be accessed easily: i.e. calling motor_arr[0] will call M1_1 and motor_arr[1] M1_2.

```c
static void unlock_all_motor()
{
    // set all motor forward to unlock
   uint32_t i;
    for (i = 0; i < MOTOR_NUMBER; ++i)
    {
        unlock_motor(i);
    }
}
```

this function cycles through all the motors and set the direction as forward which should unlock them on the exo.

NOTE: direction will depend on how the motors are wired physically. Ideally you should fix the connection at the motor connector side.

```c
void unlock_motor(uint8_t motor_idx)
{
    // set motor forward
    nrf_gpio_pin_write(motor_idx * 2, 1);
    nrf_gpio_pin_write(motor_idx * 2 + 1, 0);
}

static void lock_motor(uint8_t motor_idx)
{
    // set motor backward
    nrf_gpio_pin_write(motor_idx * 2, 0);
    nrf_gpio_pin_write(motor_idx * 2 + 1, 1);
}

static void release_motor(uint8_t motor_idx)
{
    // set motor release
    nrf_gpio_pin_write(motor_idx * 2, 0);
    nrf_gpio_pin_write(motor_idx * 2 + 1, 0);
}

static void brake_motor(uint8_t motor_idx)
{
    // set motor brake
    nrf_gpio_pin_write(motor_idx * 2, 1);
    nrf_gpio_pin_write(motor_idx * 2 + 1, 1);
}
```

The set of 4 functions are following the DRV8837 motor driver specs. Since each motor have 2 pins which are stored in motor_arr[], we need to multiply by 2 the get the correct pin assignment stored in the latter array.

```c
static void update_motors()
{
    uint8_t i;
    for (i = 0; i < MOTOR_NUMBER; ++i)
    {
        if (motors[i] == 1 && motors [i] != motors_prev[i])       // lock motor
        {
            lock_motor(i);
            motors_prev[i] = motors[i];
        }
        else if (motors[i] == 0 && motors [i] != motors_prev[i])  // unlock motor
        {
            unlock_motor(i);
            motors_prev[i] = motors[i];
        }
    }
}
```

`update_motors()` drives the motors depending on their state and previous state, which prevents the need to update every one of them at every call.

#### BLE functions

```c
static void led_write_handler(uint16_t conn_handle, ble_lbs_t * p_lbs, uint16_t msb, uint8_t lsb)
{
    NRF_LOG_INFO("BLE receive: %u and %u", msb, lsb);
    
    // Mode select
    dextrEMS_mode = ((msb>>3)&1);

    // MSB data
    motors[0] = ((msb>>1)&1);
    motors[1] = ((msb>>0)&1);

    // LSB data
    motors[2] = ((lsb>>7)&1);
    motors[3] = ((lsb>>6)&1);
    motors[4] = ((lsb>>5)&1);
    motors[5] = ((lsb>>4)&1);
    motors[6] = ((lsb>>3)&1);
    motors[7] = ((lsb>>2)&1);
    motors[8] = ((lsb>>1)&1);
    motors[9] = ((lsb>>0)&1);

    update_motors();

    // print incoming command
    NRF_LOG_INFO("Mode: %d", dextrEMS_mode);
    NRF_LOG_INFO("Binary: %u %u %u %u %u", motors[0], motors[1], motors[2], motors[3], motors[4]);
    NRF_LOG_INFO("Binary: %u %u %u %u %u", motors[5], motors[6], motors[7], motors[8], motors[9]);
}
```

This handler is called every time the nRF is receiving a BLE message. The message should come in 2 bytes hence why we have a MSByte and LSByte. This function is bit shifting the values to retrieve the motor states and storing them into the motors[] array. At the end, `update_motors()` implements the new motor states to the motor drivers.

```c
// Print incoming data. Can be called in ble_lbs.c
void debug_handler(uint16_t incoming_msg) {
   NRF_LOG_INFO("other messages: %d", incoming_msg);
}
```

This function is meant for debugging. It helps print the incoming messages received in `ble_lbs.c` to the RTT log (which can only be called in `main.c`)

In `ble_lbs.c`:

```c
static void on_write(ble_lbs_t * p_lbs, ble_evt_t const * p_ble_evt)
{
    ble_gatts_evt_write_t const * p_evt_write = &p_ble_evt->evt.gatts_evt.params.write;

    if (   (p_evt_write->handle == p_lbs->led_char_handles.value_handle)
        && (p_evt_write->len == 2) // 2 to receive 2 uint8_t packets
        && (p_lbs->led_write_handler != NULL))
    {
        p_lbs->led_write_handler(p_ble_evt->evt.gap_evt.conn_handle, p_lbs, p_evt_write->data[0], p_evt_write->data[1]); //Sending left and right bytes seperated
    }
    else {
//        debug_handler(p_evt_write->len);
    }
}
```

This function is called whenever the nRF receives a *write* value (incoming message).  It is checking if the incoming data contains 2 bytes before calling the `led_write_handler` handler. The incoming data are stored in `p_evt_write->data[]` where index `0` is the MSByte.

**Note**: this function is part of the nRF SDK, hence being shared over other projects. Before building for dextrEMS or other BLE projects based on *BLE_Blinky*, make sure you check what is inside this function.

#### Initialization/main loop

The main function starts with:

```c
// Initialize.
    log_init();
    //leds_init();
    timers_init();
    buttons_init();
    power_management_init();
    ble_stack_init();
    gap_params_init();
    gatt_init();
    services_init();
    advertising_init();
    conn_params_init();

    // motors init
    motor_init();
```

dextrEMS is not using the LEDs defined in the blinky app, hence we have to **not** initialize the *`leds_init()`*. The LED pin assignments overlaps with the motors. Furthermore, we also comment out the LED commands in the `advertising_start` and `ble_evt_handler`. To make sure you haven't missed any, search for `bsp_board_led` (`bsp_board_led_on` and `bsp_board_led_off`) which is the function used to turn on/off the LEDs

```c
// Start execution.
    NRF_LOG_INFO("dextrEMS started.");
    advertising_start();
    unlock_all_motor();
```

`advertising_start` starts the BLE advertisement.

`unlock_all_motor` unlocks all the motors.

```c
// Enter main loop.
    for (;;)
    {
        idle_state_handle();
    }
```

This should allow the nRF to manage its power as most of the code is being written around callbacks.