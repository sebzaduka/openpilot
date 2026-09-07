#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_5615908840917548007);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_3325133064770946759);
void pose_H_mod_fun(double *state, double *out_5724271770107739515);
void pose_f_fun(double *state, double dt, double *out_6512085752749911959);
void pose_F_fun(double *state, double dt, double *out_4550780972847459878);
void pose_h_4(double *state, double *unused, double *out_8637530403510222813);
void pose_H_4(double *state, double *unused, double *out_1204250909582981291);
void pose_h_10(double *state, double *unused, double *out_408371076255569127);
void pose_H_10(double *state, double *unused, double *out_669486987569912933);
void pose_h_13(double *state, double *unused, double *out_2633952316633081407);
void pose_H_13(double *state, double *unused, double *out_4416524734915314092);
void pose_h_14(double *state, double *unused, double *out_5630345490908546158);
void pose_H_14(double *state, double *unused, double *out_5167491765922465820);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}