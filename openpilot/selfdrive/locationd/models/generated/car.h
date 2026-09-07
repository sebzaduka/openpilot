#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_err_fun(double *nom_x, double *delta_x, double *out_6846017880765690011);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_7814471114123776621);
void car_H_mod_fun(double *state, double *out_3746433966412820436);
void car_f_fun(double *state, double dt, double *out_2297484923001034770);
void car_F_fun(double *state, double dt, double *out_8667372284745360037);
void car_h_25(double *state, double *unused, double *out_5923466158574376379);
void car_H_25(double *state, double *unused, double *out_6778972074322871375);
void car_h_24(double *state, double *unused, double *out_1117716094504579088);
void car_H_24(double *state, double *unused, double *out_8951621673328370941);
void car_h_30(double *state, double *unused, double *out_6198660220858882268);
void car_H_30(double *state, double *unused, double *out_4260639115815622748);
void car_h_26(double *state, double *unused, double *out_1196986953198036623);
void car_H_26(double *state, double *unused, double *out_7926268680512624017);
void car_h_27(double *state, double *unused, double *out_4979956305672713944);
void car_H_27(double *state, double *unused, double *out_6435402427616047659);
void car_h_29(double *state, double *unused, double *out_7180744314194180380);
void car_H_29(double *state, double *unused, double *out_3750407771501230564);
void car_h_28(double *state, double *unused, double *out_2375550984864016293);
void car_H_28(double *state, double *unused, double *out_8832806788570761138);
void car_h_31(double *state, double *unused, double *out_3659166490242154051);
void car_H_31(double *state, double *unused, double *out_7300060578279272541);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}