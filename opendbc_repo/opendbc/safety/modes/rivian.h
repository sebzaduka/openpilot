#pragma once

#include "opendbc/safety/declarations.h"

#define RIVIAN_COMMON_RX_CHECKS \
  {.msg = {{0x208, 0, 8, 50U, .max_counter = 14U}, { 0 }, { 0 }}},                                                             /* ESP_Status (speed) */                         \
  {.msg = {{0x150, 0, 7, 50U, .max_counter = 14U}, { 0 }, { 0 }}},                                                             /* VDM_PropStatus (gas pedal & 2nd speed) */     \
  {.msg = {{0x380, 0, 5, 100U, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true}, { 0 }, { 0 }}},  /* EPAS_SystemStatus (driver torque) */          \
  {.msg = {{0x390, 0, 7, 100U, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true}, { 0 }, { 0 }}},  /* EPAS_AdasStatus (measured angle) */           \
  {.msg = {{0x38f, 0, 6, 50U, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true}, { 0 }, { 0 }}},   /* iBESP2 (brakes) */                            \
  {.msg = {{0x100, 2, 8, 100U, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true}, { 0 }, { 0 }}},  /* ACM_Status (cruise state) */                  \

#define RIVIAN_WHEEL_BUTTONS_ADDR_CHECK \
  {.msg = {{0x131A, 1, 7, 10U, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true}, { 0 }, { 0 }}},  /* WheelButtons_Fwd */ \

#define RIVIAN_TRAILER_STATUS_ADDR_CHECK \
  {.msg = {{0x180, 0, 8, 10U, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true}, { 0 }, { 0 }}},  /* VDM_CGM_GW */ \

static bool rivian_right_scroll_pressed_prev = false;
static bool rivian_right_scroll_long_press_triggered = false;
static bool rivian_right_scroll_blocked_until_release = false;
static bool rivian_right_scroll_timing_active = false;
static bool rivian_trailer_status_seen = false;
static bool rivian_trailer_absent = false;
static uint32_t rivian_right_scroll_press_ts = 0U;

static uint8_t rivian_get_counter(const CANPacket_t *msg) {
  // Signal: ESP_Status_Counter, VDM_PropStatus_Counter
  return msg->data[1] & 0xFU;
}

static uint32_t rivian_get_checksum(const CANPacket_t *msg) {
  // Signal: ESP_Status_Checksum, VDM_PropStatus_Checksum
  return msg->data[0];
}

static uint8_t _rivian_compute_checksum(const CANPacket_t *msg, uint8_t poly, uint8_t xor_output) {
  int len = GET_LEN(msg);

  uint8_t crc = 0;
  // Skip the checksum byte
  for (int i = 1; i < len; i++) {
    crc ^= msg->data[i];
    for (int j = 0; j < 8; j++) {
      if ((crc & 0x80U) != 0U) {
        crc = (crc << 1) ^ poly;
      } else {
        crc <<= 1;
      }
    }
  }
  return crc ^ xor_output;
}

static uint32_t rivian_compute_checksum(const CANPacket_t *msg) {
  uint8_t chksum = 0;
  if (msg->addr == 0x208U) {
    chksum = _rivian_compute_checksum(msg, 0x1D, 0xB1);
  } else if (msg->addr == 0x150U) {
    chksum = _rivian_compute_checksum(msg, 0x1D, 0x9A);
  } else {
  }
  return chksum;
}

static bool rivian_get_quality_flag_valid(const CANPacket_t *msg) {
  bool valid = false;
  if (msg->addr == 0x208U) {
    valid = ((msg->data[3] >> 3) & 0x3U) == 0x1U;  // ESP_Vehicle_Speed_Q
  } else if (msg->addr == 0x150U) {
    valid = (msg->data[1] >> 6) == 0x1U;  // VDM_VehicleSpeedQ
  } else {
  }
  return valid;
}

static void rivian_rx_hook(const CANPacket_t *msg) {
  const uint32_t RIVIAN_RIGHT_SCROLL_LONG_PRESS_US = 1000000U;

  if (msg->bus == 0U)  {
    // Vehicle speed
    if (msg->addr == 0x208U) {
      float speed = ((msg->data[6] << 8) | msg->data[7]) * 0.01;
      vehicle_moving = speed > 0.0;
      UPDATE_VEHICLE_SPEED(speed * KPH_TO_MS);
    }

    // Gas pressed and second speed source for variable torque limit
    if (msg->addr == 0x150U) {
      gas_pressed = msg->data[3] | (msg->data[4] & 0xC0U);

      // Disable controls if speeds from VDM and ESP ECUs are too far apart.
      float vdm_speed = ((msg->data[5] << 8) | msg->data[6]) * 0.01 * KPH_TO_MS;
      speed_mismatch_check(vdm_speed);
    }

    // Driver torque
    if (msg->addr == 0x380U) {
      int torque_driver_new = (((msg->data[2] << 4) | (msg->data[3] >> 4))) - 2050U;
      update_sample(&torque_driver, torque_driver_new);
    }

    // Measured steering angle from EPAS (EPAS_AdasStatus)
    if (msg->addr == 0x390U) {
      // EPAS_InternalSas: 47|14@0+ (0.1,-819.2) deg
      // Stored as degrees * 10 to match angle_deg_to_can
      int angle_meas_new = ((msg->data[5] << 6) | (msg->data[6] >> 2)) - 8192U;
      update_sample(&angle_meas, angle_meas_new);
    }

    // Brake pressed
    if (msg->addr == 0x38fU) {
      brake_pressed = (msg->data[2] >> 7) & 1U;
    }

    if (msg->addr == 0x180U) {
      // CGM_TrailerPresent: 0=not present, 1=present, 3=invalid
      const uint8_t trailer_status = (msg->data[1] >> 4) & 0x3U;
      rivian_trailer_status_seen = true;
      rivian_trailer_absent = trailer_status == 0U;
      if (!rivian_trailer_absent && rivian_right_scroll_pressed_prev) {
        rivian_right_scroll_press_ts = 0U;
        rivian_right_scroll_timing_active = false;
        rivian_right_scroll_long_press_triggered = false;
        rivian_right_scroll_blocked_until_release = true;
        mads_button_press = MADS_BUTTON_NOT_PRESSED;
      }
    }
  }

  if (msg->bus == 2U) {
    // Cruise state
    if (msg->addr == 0x100U) {
      const int feature_status = msg->data[2] >> 5U;
      pcm_cruise_check(feature_status == 1);
    }
  }

  if ((msg->bus == 1U) && (msg->addr == 0x131AU)) {
    const bool right_scroll_pressed = ((msg->data[4] >> 2) & 0x3U) == 2U;
    const uint32_t now = microsecond_timer_get();

    if (!right_scroll_pressed) {
      rivian_right_scroll_press_ts = 0U;
      rivian_right_scroll_timing_active = false;
      rivian_right_scroll_long_press_triggered = false;
      rivian_right_scroll_blocked_until_release = false;
      mads_button_press = MADS_BUTTON_NOT_PRESSED;
    } else if (rivian_trailer_status_seen && !rivian_trailer_absent) {
      rivian_right_scroll_press_ts = 0U;
      rivian_right_scroll_timing_active = false;
      rivian_right_scroll_long_press_triggered = false;
      rivian_right_scroll_blocked_until_release = true;
      mads_button_press = MADS_BUTTON_NOT_PRESSED;
    } else if (rivian_right_scroll_blocked_until_release) {
      mads_button_press = MADS_BUTTON_NOT_PRESSED;
    } else if (!rivian_trailer_status_seen) {
      rivian_right_scroll_press_ts = 0U;
      rivian_right_scroll_timing_active = false;
      rivian_right_scroll_long_press_triggered = false;
      mads_button_press = MADS_BUTTON_NOT_PRESSED;
    } else {
      if (!rivian_right_scroll_timing_active) {
        rivian_right_scroll_press_ts = now;
        rivian_right_scroll_timing_active = true;
      }

      const bool long_press = safety_get_ts_elapsed(now, rivian_right_scroll_press_ts) >= RIVIAN_RIGHT_SCROLL_LONG_PRESS_US;
      if (long_press && !rivian_right_scroll_long_press_triggered) {
        rivian_right_scroll_long_press_triggered = true;
        if (m_mads_state.system_enabled) {
          if (controls_allowed || controls_allowed_lateral) {
            controls_allowed = false;
            mads_exit_controls(MADS_DISENGAGE_REASON_BUTTON);
            mads_button_press = MADS_BUTTON_NOT_PRESSED;
          } else {
            mads_button_press = MADS_BUTTON_PRESSED;
          }
        }
      }
    }

    rivian_right_scroll_pressed_prev = right_scroll_pressed;
  }
}

static bool rivian_tx_hook(const CANPacket_t *msg) {
  const AngleSteeringLimits RIVIAN_ANGLE_STEERING_LIMITS = {
    .max_angle = 5000,  // 500 deg
    .angle_deg_to_can = 10,
    .frequency = 100U,
  };

  const AngleSteeringParams RIVIAN_ANGLE_STEERING_PARAMS = {
    .slip_factor = -0.0005445721739802007,
    .steer_ratio = 15.2,
    .wheelbase = 3.08,
  };

  const TorqueSteeringLimits RIVIAN_STEERING_LIMITS = {
    .max_torque = 350,
    .dynamic_max_torque = true,
    .max_torque_lookup = {
      {9., 17., 17.},
      {350, 250, 250},
    },
    .max_rate_up = 3,
    .max_rate_down = 5,
    .max_rt_delta = 125,
    .driver_torque_multiplier = 2,
    .driver_torque_allowance = 100,
    .type = TorqueDriverLimited,

    .min_valid_request_frames = 89,
    .max_invalid_request_frames = 2,
    .min_valid_request_rt_interval = 810000,  // 810ms, a ~10% buffer on cutting every 90 frames
    .has_steer_req_tolerance = true,
  };

  const LongitudinalLimits RIVIAN_LONG_LIMITS = {
    .max_accel = 200,
    .min_accel = -350,
    .inactive_accel = 0,
  };

  bool tx = true;

  if (msg->bus == 0U) {
    // Angle steering control
    if (msg->addr == 0x110U) {
      int desired_angle = ((msg->data[2] << 7) | (msg->data[3] >> 1)) - 16384U;
      bool lka_active = GET_BIT(msg, 12U);

      if (steer_angle_cmd_checks_vm(desired_angle, lka_active, RIVIAN_ANGLE_STEERING_LIMITS, RIVIAN_ANGLE_STEERING_PARAMS)) {
        tx = false;
      }
    }

    // Torque steering control (cooperative override)
    if (msg->addr == 0x120U) {
      int desired_torque = ((msg->data[2] << 3U) | (msg->data[3] >> 5U)) - 1024U;
      bool steer_req = (msg->data[3] >> 4) & 1U;

      if (steer_torque_cmd_checks(desired_torque, steer_req, RIVIAN_STEERING_LIMITS)) {
        tx = false;
      }
    }

    // Longitudinal control
    if (msg->addr == 0x160U) {
      int raw_accel = ((msg->data[2] << 3) | (msg->data[3] >> 5)) - 1024U;
      if (longitudinal_accel_checks(raw_accel, RIVIAN_LONG_LIMITS)) {
        tx = false;
      }
    }
  }

  return tx;
}

static safety_config rivian_init(uint16_t param) {
  // SCCM_WheelTouch: for hiding hold wheel alert
  // VDM_AdasSts: for canceling stock ACC
  // 0x100 = ACM_Status, 0x110 = ACM_SteeringControl, 0x120 = ACM_lkaHbaCmd, 0x321 = SCCM_WheelTouch, 0x162 = VDM_AdasSts
  static const CanMsg RIVIAN_TX_MSGS[] = {{0x100, 0, 8, .check_relay = true}, {0x110, 0, 8, .check_relay = true}, {0x120, 0, 8, .check_relay = true}, {0x321, 2, 7, .check_relay = true}, {0x162, 2, 8, .check_relay = true}};
  // 0x160 = ACM_longitudinalRequest, 0x162 = VDM_AdasSts
  static const CanMsg RIVIAN_LONG_TX_MSGS[] = {{0x100, 0, 8, .check_relay = true}, {0x110, 0, 8, .check_relay = true}, {0x120, 0, 8, .check_relay = true}, {0x321, 2, 7, .check_relay = true}, {0x160, 0, 5, .check_relay = true}, {0x162, 2, 8, .check_relay = true}};

  static RxCheck rivian_rx_checks[] = {
    RIVIAN_COMMON_RX_CHECKS
  };

  static RxCheck rivian_wheel_buttons_rx_checks[] = {
    RIVIAN_COMMON_RX_CHECKS
    RIVIAN_WHEEL_BUTTONS_ADDR_CHECK
    RIVIAN_TRAILER_STATUS_ADDR_CHECK
  };

  bool rivian_longitudinal = false;
  const uint16_t RIVIAN_PARAM_SP_LONGITUDINAL_HARNESS_UPGRADE = 1U;
  const bool rivian_has_wheel_buttons = GET_FLAG(current_safety_param_sp, RIVIAN_PARAM_SP_LONGITUDINAL_HARNESS_UPGRADE);

  rivian_right_scroll_pressed_prev = false;
  rivian_right_scroll_long_press_triggered = false;
  rivian_right_scroll_blocked_until_release = false;
  rivian_right_scroll_timing_active = false;
  rivian_trailer_status_seen = false;
  rivian_trailer_absent = false;
  rivian_right_scroll_press_ts = 0U;
  mads_button_press = MADS_BUTTON_UNAVAILABLE;

  SAFETY_UNUSED(param);
  #ifdef ALLOW_DEBUG
    const int FLAG_RIVIAN_LONG_CONTROL = 1;
    rivian_longitudinal = GET_FLAG(param, FLAG_RIVIAN_LONG_CONTROL);
  #endif

  // FIXME: cppcheck thinks that rivian_longitudinal is always false. This is not true
  // if ALLOW_DEBUG is defined but cppcheck is run without ALLOW_DEBUG
  // cppcheck-suppress knownConditionTrueFalse
  safety_config ret;
  if (rivian_longitudinal) {
    SET_TX_MSGS(RIVIAN_LONG_TX_MSGS, ret);
  } else {
    SET_TX_MSGS(RIVIAN_TX_MSGS, ret);
  }

  if (rivian_has_wheel_buttons) {
    SET_RX_CHECKS(rivian_wheel_buttons_rx_checks, ret);
  } else {
    SET_RX_CHECKS(rivian_rx_checks, ret);
  }
  return ret;
}

const safety_hooks rivian_hooks = {
  .init = rivian_init,
  .rx = rivian_rx_hook,
  .tx = rivian_tx_hook,
  .get_counter = rivian_get_counter,
  .get_checksum = rivian_get_checksum,
  .compute_checksum = rivian_compute_checksum,
  .get_quality_flag_valid = rivian_get_quality_flag_valid,
};
