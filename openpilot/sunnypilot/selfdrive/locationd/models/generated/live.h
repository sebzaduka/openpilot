#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void live_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_9(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_12(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_35(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_32(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_33(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_H(double *in_vec, double *out_6380853900073817641);
void live_err_fun(double *nom_x, double *delta_x, double *out_7427762876798338975);
void live_inv_err_fun(double *nom_x, double *true_x, double *out_4729337405393182619);
void live_H_mod_fun(double *state, double *out_6378663054825410066);
void live_f_fun(double *state, double dt, double *out_5841588921433961672);
void live_F_fun(double *state, double dt, double *out_8111201984892693236);
void live_h_4(double *state, double *unused, double *out_2271759915752757158);
void live_H_4(double *state, double *unused, double *out_416815848262321087);
void live_h_9(double *state, double *unused, double *out_8736469226955104412);
void live_H_9(double *state, double *unused, double *out_7704034783526768557);
void live_h_10(double *state, double *unused, double *out_7747671888616415891);
void live_H_10(double *state, double *unused, double *out_1603982038820452539);
void live_h_12(double *state, double *unused, double *out_2765575514199653704);
void live_H_12(double *state, double *unused, double *out_5436272256294282882);
void live_h_35(double *state, double *unused, double *out_7566910700143672126);
void live_H_35(double *state, double *unused, double *out_3783477905634928463);
void live_h_32(double *state, double *unused, double *out_6383508982142204427);
void live_H_32(double *state, double *unused, double *out_7869213593731851563);
void live_h_13(double *state, double *unused, double *out_2392751485065219313);
void live_H_13(double *state, double *unused, double *out_7377128500863653672);
void live_h_14(double *state, double *unused, double *out_8736469226955104412);
void live_H_14(double *state, double *unused, double *out_7704034783526768557);
void live_h_33(double *state, double *unused, double *out_8355077153134918667);
void live_H_33(double *state, double *unused, double *out_6934034910273786067);
void live_predict(double *in_x, double *in_P, double *in_Q, double dt);
}