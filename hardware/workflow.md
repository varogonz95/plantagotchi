# Workflow

## 1. Setup connection.

### A. With Access Point step only
- Create Access Point being Plantagotchi-{MAC_ADDRESS_PORTION}
- Run a minimal Web server 
- Serve a simple form to submit network credentials to connect to
- Store (and persist) credentials
- Turn WLAN connection to station (client) mode.
- Attempt to connect to stored network with SSID and PWRD
- If connected, then start monitor program
- else, show error message indicating that the connection setup was unsuccessful

### B. With BT connection step:
- Enable BT connection with burned Identifier, so it can be detected on another device
- If device paired with a Plantagotchi via BT, then:
    - Give (this) device a name
    - Continue with workflow A.
- Else, show error message

-------------------------------------------------------------------------------------------------------------

## Calibration Menu.
- In a separate thread, check for MenuButton to be pushed.
- If the button is pushed, then:
    - Show Calibration Menu:
        | Calibration Menu       |
        | ---------------------- |
        | > Light Sensor         |
        | Soil Moisture Sensor   |

### Soil Moisture Sensor Calibration.
- To calibrate `MIN_MOISTURE`, show the following message:
    > Set Min Moisture  
    >
    > Voltage: `{soil_sensor.read_uv()}`  
    > \> Press [BUTTON]  
    > to calibrate
- When [BUTTON] is pressed, set `MIN_MOISTURE` to `soil.read_uv()` value