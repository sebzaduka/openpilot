#include "pose.h"

namespace {
#define DIM 18
#define EDIM 18
#define MEDIM 18
typedef void (*Hfun)(double *, double *, double *);
const static double MAHA_THRESH_4 = 7.814727903251177;
const static double MAHA_THRESH_10 = 7.814727903251177;
const static double MAHA_THRESH_13 = 7.814727903251177;
const static double MAHA_THRESH_14 = 7.814727903251177;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_5615908840917548007) {
   out_5615908840917548007[0] = delta_x[0] + nom_x[0];
   out_5615908840917548007[1] = delta_x[1] + nom_x[1];
   out_5615908840917548007[2] = delta_x[2] + nom_x[2];
   out_5615908840917548007[3] = delta_x[3] + nom_x[3];
   out_5615908840917548007[4] = delta_x[4] + nom_x[4];
   out_5615908840917548007[5] = delta_x[5] + nom_x[5];
   out_5615908840917548007[6] = delta_x[6] + nom_x[6];
   out_5615908840917548007[7] = delta_x[7] + nom_x[7];
   out_5615908840917548007[8] = delta_x[8] + nom_x[8];
   out_5615908840917548007[9] = delta_x[9] + nom_x[9];
   out_5615908840917548007[10] = delta_x[10] + nom_x[10];
   out_5615908840917548007[11] = delta_x[11] + nom_x[11];
   out_5615908840917548007[12] = delta_x[12] + nom_x[12];
   out_5615908840917548007[13] = delta_x[13] + nom_x[13];
   out_5615908840917548007[14] = delta_x[14] + nom_x[14];
   out_5615908840917548007[15] = delta_x[15] + nom_x[15];
   out_5615908840917548007[16] = delta_x[16] + nom_x[16];
   out_5615908840917548007[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_3325133064770946759) {
   out_3325133064770946759[0] = -nom_x[0] + true_x[0];
   out_3325133064770946759[1] = -nom_x[1] + true_x[1];
   out_3325133064770946759[2] = -nom_x[2] + true_x[2];
   out_3325133064770946759[3] = -nom_x[3] + true_x[3];
   out_3325133064770946759[4] = -nom_x[4] + true_x[4];
   out_3325133064770946759[5] = -nom_x[5] + true_x[5];
   out_3325133064770946759[6] = -nom_x[6] + true_x[6];
   out_3325133064770946759[7] = -nom_x[7] + true_x[7];
   out_3325133064770946759[8] = -nom_x[8] + true_x[8];
   out_3325133064770946759[9] = -nom_x[9] + true_x[9];
   out_3325133064770946759[10] = -nom_x[10] + true_x[10];
   out_3325133064770946759[11] = -nom_x[11] + true_x[11];
   out_3325133064770946759[12] = -nom_x[12] + true_x[12];
   out_3325133064770946759[13] = -nom_x[13] + true_x[13];
   out_3325133064770946759[14] = -nom_x[14] + true_x[14];
   out_3325133064770946759[15] = -nom_x[15] + true_x[15];
   out_3325133064770946759[16] = -nom_x[16] + true_x[16];
   out_3325133064770946759[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_5724271770107739515) {
   out_5724271770107739515[0] = 1.0;
   out_5724271770107739515[1] = 0.0;
   out_5724271770107739515[2] = 0.0;
   out_5724271770107739515[3] = 0.0;
   out_5724271770107739515[4] = 0.0;
   out_5724271770107739515[5] = 0.0;
   out_5724271770107739515[6] = 0.0;
   out_5724271770107739515[7] = 0.0;
   out_5724271770107739515[8] = 0.0;
   out_5724271770107739515[9] = 0.0;
   out_5724271770107739515[10] = 0.0;
   out_5724271770107739515[11] = 0.0;
   out_5724271770107739515[12] = 0.0;
   out_5724271770107739515[13] = 0.0;
   out_5724271770107739515[14] = 0.0;
   out_5724271770107739515[15] = 0.0;
   out_5724271770107739515[16] = 0.0;
   out_5724271770107739515[17] = 0.0;
   out_5724271770107739515[18] = 0.0;
   out_5724271770107739515[19] = 1.0;
   out_5724271770107739515[20] = 0.0;
   out_5724271770107739515[21] = 0.0;
   out_5724271770107739515[22] = 0.0;
   out_5724271770107739515[23] = 0.0;
   out_5724271770107739515[24] = 0.0;
   out_5724271770107739515[25] = 0.0;
   out_5724271770107739515[26] = 0.0;
   out_5724271770107739515[27] = 0.0;
   out_5724271770107739515[28] = 0.0;
   out_5724271770107739515[29] = 0.0;
   out_5724271770107739515[30] = 0.0;
   out_5724271770107739515[31] = 0.0;
   out_5724271770107739515[32] = 0.0;
   out_5724271770107739515[33] = 0.0;
   out_5724271770107739515[34] = 0.0;
   out_5724271770107739515[35] = 0.0;
   out_5724271770107739515[36] = 0.0;
   out_5724271770107739515[37] = 0.0;
   out_5724271770107739515[38] = 1.0;
   out_5724271770107739515[39] = 0.0;
   out_5724271770107739515[40] = 0.0;
   out_5724271770107739515[41] = 0.0;
   out_5724271770107739515[42] = 0.0;
   out_5724271770107739515[43] = 0.0;
   out_5724271770107739515[44] = 0.0;
   out_5724271770107739515[45] = 0.0;
   out_5724271770107739515[46] = 0.0;
   out_5724271770107739515[47] = 0.0;
   out_5724271770107739515[48] = 0.0;
   out_5724271770107739515[49] = 0.0;
   out_5724271770107739515[50] = 0.0;
   out_5724271770107739515[51] = 0.0;
   out_5724271770107739515[52] = 0.0;
   out_5724271770107739515[53] = 0.0;
   out_5724271770107739515[54] = 0.0;
   out_5724271770107739515[55] = 0.0;
   out_5724271770107739515[56] = 0.0;
   out_5724271770107739515[57] = 1.0;
   out_5724271770107739515[58] = 0.0;
   out_5724271770107739515[59] = 0.0;
   out_5724271770107739515[60] = 0.0;
   out_5724271770107739515[61] = 0.0;
   out_5724271770107739515[62] = 0.0;
   out_5724271770107739515[63] = 0.0;
   out_5724271770107739515[64] = 0.0;
   out_5724271770107739515[65] = 0.0;
   out_5724271770107739515[66] = 0.0;
   out_5724271770107739515[67] = 0.0;
   out_5724271770107739515[68] = 0.0;
   out_5724271770107739515[69] = 0.0;
   out_5724271770107739515[70] = 0.0;
   out_5724271770107739515[71] = 0.0;
   out_5724271770107739515[72] = 0.0;
   out_5724271770107739515[73] = 0.0;
   out_5724271770107739515[74] = 0.0;
   out_5724271770107739515[75] = 0.0;
   out_5724271770107739515[76] = 1.0;
   out_5724271770107739515[77] = 0.0;
   out_5724271770107739515[78] = 0.0;
   out_5724271770107739515[79] = 0.0;
   out_5724271770107739515[80] = 0.0;
   out_5724271770107739515[81] = 0.0;
   out_5724271770107739515[82] = 0.0;
   out_5724271770107739515[83] = 0.0;
   out_5724271770107739515[84] = 0.0;
   out_5724271770107739515[85] = 0.0;
   out_5724271770107739515[86] = 0.0;
   out_5724271770107739515[87] = 0.0;
   out_5724271770107739515[88] = 0.0;
   out_5724271770107739515[89] = 0.0;
   out_5724271770107739515[90] = 0.0;
   out_5724271770107739515[91] = 0.0;
   out_5724271770107739515[92] = 0.0;
   out_5724271770107739515[93] = 0.0;
   out_5724271770107739515[94] = 0.0;
   out_5724271770107739515[95] = 1.0;
   out_5724271770107739515[96] = 0.0;
   out_5724271770107739515[97] = 0.0;
   out_5724271770107739515[98] = 0.0;
   out_5724271770107739515[99] = 0.0;
   out_5724271770107739515[100] = 0.0;
   out_5724271770107739515[101] = 0.0;
   out_5724271770107739515[102] = 0.0;
   out_5724271770107739515[103] = 0.0;
   out_5724271770107739515[104] = 0.0;
   out_5724271770107739515[105] = 0.0;
   out_5724271770107739515[106] = 0.0;
   out_5724271770107739515[107] = 0.0;
   out_5724271770107739515[108] = 0.0;
   out_5724271770107739515[109] = 0.0;
   out_5724271770107739515[110] = 0.0;
   out_5724271770107739515[111] = 0.0;
   out_5724271770107739515[112] = 0.0;
   out_5724271770107739515[113] = 0.0;
   out_5724271770107739515[114] = 1.0;
   out_5724271770107739515[115] = 0.0;
   out_5724271770107739515[116] = 0.0;
   out_5724271770107739515[117] = 0.0;
   out_5724271770107739515[118] = 0.0;
   out_5724271770107739515[119] = 0.0;
   out_5724271770107739515[120] = 0.0;
   out_5724271770107739515[121] = 0.0;
   out_5724271770107739515[122] = 0.0;
   out_5724271770107739515[123] = 0.0;
   out_5724271770107739515[124] = 0.0;
   out_5724271770107739515[125] = 0.0;
   out_5724271770107739515[126] = 0.0;
   out_5724271770107739515[127] = 0.0;
   out_5724271770107739515[128] = 0.0;
   out_5724271770107739515[129] = 0.0;
   out_5724271770107739515[130] = 0.0;
   out_5724271770107739515[131] = 0.0;
   out_5724271770107739515[132] = 0.0;
   out_5724271770107739515[133] = 1.0;
   out_5724271770107739515[134] = 0.0;
   out_5724271770107739515[135] = 0.0;
   out_5724271770107739515[136] = 0.0;
   out_5724271770107739515[137] = 0.0;
   out_5724271770107739515[138] = 0.0;
   out_5724271770107739515[139] = 0.0;
   out_5724271770107739515[140] = 0.0;
   out_5724271770107739515[141] = 0.0;
   out_5724271770107739515[142] = 0.0;
   out_5724271770107739515[143] = 0.0;
   out_5724271770107739515[144] = 0.0;
   out_5724271770107739515[145] = 0.0;
   out_5724271770107739515[146] = 0.0;
   out_5724271770107739515[147] = 0.0;
   out_5724271770107739515[148] = 0.0;
   out_5724271770107739515[149] = 0.0;
   out_5724271770107739515[150] = 0.0;
   out_5724271770107739515[151] = 0.0;
   out_5724271770107739515[152] = 1.0;
   out_5724271770107739515[153] = 0.0;
   out_5724271770107739515[154] = 0.0;
   out_5724271770107739515[155] = 0.0;
   out_5724271770107739515[156] = 0.0;
   out_5724271770107739515[157] = 0.0;
   out_5724271770107739515[158] = 0.0;
   out_5724271770107739515[159] = 0.0;
   out_5724271770107739515[160] = 0.0;
   out_5724271770107739515[161] = 0.0;
   out_5724271770107739515[162] = 0.0;
   out_5724271770107739515[163] = 0.0;
   out_5724271770107739515[164] = 0.0;
   out_5724271770107739515[165] = 0.0;
   out_5724271770107739515[166] = 0.0;
   out_5724271770107739515[167] = 0.0;
   out_5724271770107739515[168] = 0.0;
   out_5724271770107739515[169] = 0.0;
   out_5724271770107739515[170] = 0.0;
   out_5724271770107739515[171] = 1.0;
   out_5724271770107739515[172] = 0.0;
   out_5724271770107739515[173] = 0.0;
   out_5724271770107739515[174] = 0.0;
   out_5724271770107739515[175] = 0.0;
   out_5724271770107739515[176] = 0.0;
   out_5724271770107739515[177] = 0.0;
   out_5724271770107739515[178] = 0.0;
   out_5724271770107739515[179] = 0.0;
   out_5724271770107739515[180] = 0.0;
   out_5724271770107739515[181] = 0.0;
   out_5724271770107739515[182] = 0.0;
   out_5724271770107739515[183] = 0.0;
   out_5724271770107739515[184] = 0.0;
   out_5724271770107739515[185] = 0.0;
   out_5724271770107739515[186] = 0.0;
   out_5724271770107739515[187] = 0.0;
   out_5724271770107739515[188] = 0.0;
   out_5724271770107739515[189] = 0.0;
   out_5724271770107739515[190] = 1.0;
   out_5724271770107739515[191] = 0.0;
   out_5724271770107739515[192] = 0.0;
   out_5724271770107739515[193] = 0.0;
   out_5724271770107739515[194] = 0.0;
   out_5724271770107739515[195] = 0.0;
   out_5724271770107739515[196] = 0.0;
   out_5724271770107739515[197] = 0.0;
   out_5724271770107739515[198] = 0.0;
   out_5724271770107739515[199] = 0.0;
   out_5724271770107739515[200] = 0.0;
   out_5724271770107739515[201] = 0.0;
   out_5724271770107739515[202] = 0.0;
   out_5724271770107739515[203] = 0.0;
   out_5724271770107739515[204] = 0.0;
   out_5724271770107739515[205] = 0.0;
   out_5724271770107739515[206] = 0.0;
   out_5724271770107739515[207] = 0.0;
   out_5724271770107739515[208] = 0.0;
   out_5724271770107739515[209] = 1.0;
   out_5724271770107739515[210] = 0.0;
   out_5724271770107739515[211] = 0.0;
   out_5724271770107739515[212] = 0.0;
   out_5724271770107739515[213] = 0.0;
   out_5724271770107739515[214] = 0.0;
   out_5724271770107739515[215] = 0.0;
   out_5724271770107739515[216] = 0.0;
   out_5724271770107739515[217] = 0.0;
   out_5724271770107739515[218] = 0.0;
   out_5724271770107739515[219] = 0.0;
   out_5724271770107739515[220] = 0.0;
   out_5724271770107739515[221] = 0.0;
   out_5724271770107739515[222] = 0.0;
   out_5724271770107739515[223] = 0.0;
   out_5724271770107739515[224] = 0.0;
   out_5724271770107739515[225] = 0.0;
   out_5724271770107739515[226] = 0.0;
   out_5724271770107739515[227] = 0.0;
   out_5724271770107739515[228] = 1.0;
   out_5724271770107739515[229] = 0.0;
   out_5724271770107739515[230] = 0.0;
   out_5724271770107739515[231] = 0.0;
   out_5724271770107739515[232] = 0.0;
   out_5724271770107739515[233] = 0.0;
   out_5724271770107739515[234] = 0.0;
   out_5724271770107739515[235] = 0.0;
   out_5724271770107739515[236] = 0.0;
   out_5724271770107739515[237] = 0.0;
   out_5724271770107739515[238] = 0.0;
   out_5724271770107739515[239] = 0.0;
   out_5724271770107739515[240] = 0.0;
   out_5724271770107739515[241] = 0.0;
   out_5724271770107739515[242] = 0.0;
   out_5724271770107739515[243] = 0.0;
   out_5724271770107739515[244] = 0.0;
   out_5724271770107739515[245] = 0.0;
   out_5724271770107739515[246] = 0.0;
   out_5724271770107739515[247] = 1.0;
   out_5724271770107739515[248] = 0.0;
   out_5724271770107739515[249] = 0.0;
   out_5724271770107739515[250] = 0.0;
   out_5724271770107739515[251] = 0.0;
   out_5724271770107739515[252] = 0.0;
   out_5724271770107739515[253] = 0.0;
   out_5724271770107739515[254] = 0.0;
   out_5724271770107739515[255] = 0.0;
   out_5724271770107739515[256] = 0.0;
   out_5724271770107739515[257] = 0.0;
   out_5724271770107739515[258] = 0.0;
   out_5724271770107739515[259] = 0.0;
   out_5724271770107739515[260] = 0.0;
   out_5724271770107739515[261] = 0.0;
   out_5724271770107739515[262] = 0.0;
   out_5724271770107739515[263] = 0.0;
   out_5724271770107739515[264] = 0.0;
   out_5724271770107739515[265] = 0.0;
   out_5724271770107739515[266] = 1.0;
   out_5724271770107739515[267] = 0.0;
   out_5724271770107739515[268] = 0.0;
   out_5724271770107739515[269] = 0.0;
   out_5724271770107739515[270] = 0.0;
   out_5724271770107739515[271] = 0.0;
   out_5724271770107739515[272] = 0.0;
   out_5724271770107739515[273] = 0.0;
   out_5724271770107739515[274] = 0.0;
   out_5724271770107739515[275] = 0.0;
   out_5724271770107739515[276] = 0.0;
   out_5724271770107739515[277] = 0.0;
   out_5724271770107739515[278] = 0.0;
   out_5724271770107739515[279] = 0.0;
   out_5724271770107739515[280] = 0.0;
   out_5724271770107739515[281] = 0.0;
   out_5724271770107739515[282] = 0.0;
   out_5724271770107739515[283] = 0.0;
   out_5724271770107739515[284] = 0.0;
   out_5724271770107739515[285] = 1.0;
   out_5724271770107739515[286] = 0.0;
   out_5724271770107739515[287] = 0.0;
   out_5724271770107739515[288] = 0.0;
   out_5724271770107739515[289] = 0.0;
   out_5724271770107739515[290] = 0.0;
   out_5724271770107739515[291] = 0.0;
   out_5724271770107739515[292] = 0.0;
   out_5724271770107739515[293] = 0.0;
   out_5724271770107739515[294] = 0.0;
   out_5724271770107739515[295] = 0.0;
   out_5724271770107739515[296] = 0.0;
   out_5724271770107739515[297] = 0.0;
   out_5724271770107739515[298] = 0.0;
   out_5724271770107739515[299] = 0.0;
   out_5724271770107739515[300] = 0.0;
   out_5724271770107739515[301] = 0.0;
   out_5724271770107739515[302] = 0.0;
   out_5724271770107739515[303] = 0.0;
   out_5724271770107739515[304] = 1.0;
   out_5724271770107739515[305] = 0.0;
   out_5724271770107739515[306] = 0.0;
   out_5724271770107739515[307] = 0.0;
   out_5724271770107739515[308] = 0.0;
   out_5724271770107739515[309] = 0.0;
   out_5724271770107739515[310] = 0.0;
   out_5724271770107739515[311] = 0.0;
   out_5724271770107739515[312] = 0.0;
   out_5724271770107739515[313] = 0.0;
   out_5724271770107739515[314] = 0.0;
   out_5724271770107739515[315] = 0.0;
   out_5724271770107739515[316] = 0.0;
   out_5724271770107739515[317] = 0.0;
   out_5724271770107739515[318] = 0.0;
   out_5724271770107739515[319] = 0.0;
   out_5724271770107739515[320] = 0.0;
   out_5724271770107739515[321] = 0.0;
   out_5724271770107739515[322] = 0.0;
   out_5724271770107739515[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_6512085752749911959) {
   out_6512085752749911959[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_6512085752749911959[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_6512085752749911959[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_6512085752749911959[3] = dt*state[12] + state[3];
   out_6512085752749911959[4] = dt*state[13] + state[4];
   out_6512085752749911959[5] = dt*state[14] + state[5];
   out_6512085752749911959[6] = state[6];
   out_6512085752749911959[7] = state[7];
   out_6512085752749911959[8] = state[8];
   out_6512085752749911959[9] = state[9];
   out_6512085752749911959[10] = state[10];
   out_6512085752749911959[11] = state[11];
   out_6512085752749911959[12] = state[12];
   out_6512085752749911959[13] = state[13];
   out_6512085752749911959[14] = state[14];
   out_6512085752749911959[15] = state[15];
   out_6512085752749911959[16] = state[16];
   out_6512085752749911959[17] = state[17];
}
void F_fun(double *state, double dt, double *out_4550780972847459878) {
   out_4550780972847459878[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4550780972847459878[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4550780972847459878[2] = 0;
   out_4550780972847459878[3] = 0;
   out_4550780972847459878[4] = 0;
   out_4550780972847459878[5] = 0;
   out_4550780972847459878[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4550780972847459878[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4550780972847459878[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4550780972847459878[9] = 0;
   out_4550780972847459878[10] = 0;
   out_4550780972847459878[11] = 0;
   out_4550780972847459878[12] = 0;
   out_4550780972847459878[13] = 0;
   out_4550780972847459878[14] = 0;
   out_4550780972847459878[15] = 0;
   out_4550780972847459878[16] = 0;
   out_4550780972847459878[17] = 0;
   out_4550780972847459878[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4550780972847459878[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4550780972847459878[20] = 0;
   out_4550780972847459878[21] = 0;
   out_4550780972847459878[22] = 0;
   out_4550780972847459878[23] = 0;
   out_4550780972847459878[24] = 0;
   out_4550780972847459878[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4550780972847459878[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4550780972847459878[27] = 0;
   out_4550780972847459878[28] = 0;
   out_4550780972847459878[29] = 0;
   out_4550780972847459878[30] = 0;
   out_4550780972847459878[31] = 0;
   out_4550780972847459878[32] = 0;
   out_4550780972847459878[33] = 0;
   out_4550780972847459878[34] = 0;
   out_4550780972847459878[35] = 0;
   out_4550780972847459878[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4550780972847459878[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4550780972847459878[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4550780972847459878[39] = 0;
   out_4550780972847459878[40] = 0;
   out_4550780972847459878[41] = 0;
   out_4550780972847459878[42] = 0;
   out_4550780972847459878[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4550780972847459878[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4550780972847459878[45] = 0;
   out_4550780972847459878[46] = 0;
   out_4550780972847459878[47] = 0;
   out_4550780972847459878[48] = 0;
   out_4550780972847459878[49] = 0;
   out_4550780972847459878[50] = 0;
   out_4550780972847459878[51] = 0;
   out_4550780972847459878[52] = 0;
   out_4550780972847459878[53] = 0;
   out_4550780972847459878[54] = 0;
   out_4550780972847459878[55] = 0;
   out_4550780972847459878[56] = 0;
   out_4550780972847459878[57] = 1;
   out_4550780972847459878[58] = 0;
   out_4550780972847459878[59] = 0;
   out_4550780972847459878[60] = 0;
   out_4550780972847459878[61] = 0;
   out_4550780972847459878[62] = 0;
   out_4550780972847459878[63] = 0;
   out_4550780972847459878[64] = 0;
   out_4550780972847459878[65] = 0;
   out_4550780972847459878[66] = dt;
   out_4550780972847459878[67] = 0;
   out_4550780972847459878[68] = 0;
   out_4550780972847459878[69] = 0;
   out_4550780972847459878[70] = 0;
   out_4550780972847459878[71] = 0;
   out_4550780972847459878[72] = 0;
   out_4550780972847459878[73] = 0;
   out_4550780972847459878[74] = 0;
   out_4550780972847459878[75] = 0;
   out_4550780972847459878[76] = 1;
   out_4550780972847459878[77] = 0;
   out_4550780972847459878[78] = 0;
   out_4550780972847459878[79] = 0;
   out_4550780972847459878[80] = 0;
   out_4550780972847459878[81] = 0;
   out_4550780972847459878[82] = 0;
   out_4550780972847459878[83] = 0;
   out_4550780972847459878[84] = 0;
   out_4550780972847459878[85] = dt;
   out_4550780972847459878[86] = 0;
   out_4550780972847459878[87] = 0;
   out_4550780972847459878[88] = 0;
   out_4550780972847459878[89] = 0;
   out_4550780972847459878[90] = 0;
   out_4550780972847459878[91] = 0;
   out_4550780972847459878[92] = 0;
   out_4550780972847459878[93] = 0;
   out_4550780972847459878[94] = 0;
   out_4550780972847459878[95] = 1;
   out_4550780972847459878[96] = 0;
   out_4550780972847459878[97] = 0;
   out_4550780972847459878[98] = 0;
   out_4550780972847459878[99] = 0;
   out_4550780972847459878[100] = 0;
   out_4550780972847459878[101] = 0;
   out_4550780972847459878[102] = 0;
   out_4550780972847459878[103] = 0;
   out_4550780972847459878[104] = dt;
   out_4550780972847459878[105] = 0;
   out_4550780972847459878[106] = 0;
   out_4550780972847459878[107] = 0;
   out_4550780972847459878[108] = 0;
   out_4550780972847459878[109] = 0;
   out_4550780972847459878[110] = 0;
   out_4550780972847459878[111] = 0;
   out_4550780972847459878[112] = 0;
   out_4550780972847459878[113] = 0;
   out_4550780972847459878[114] = 1;
   out_4550780972847459878[115] = 0;
   out_4550780972847459878[116] = 0;
   out_4550780972847459878[117] = 0;
   out_4550780972847459878[118] = 0;
   out_4550780972847459878[119] = 0;
   out_4550780972847459878[120] = 0;
   out_4550780972847459878[121] = 0;
   out_4550780972847459878[122] = 0;
   out_4550780972847459878[123] = 0;
   out_4550780972847459878[124] = 0;
   out_4550780972847459878[125] = 0;
   out_4550780972847459878[126] = 0;
   out_4550780972847459878[127] = 0;
   out_4550780972847459878[128] = 0;
   out_4550780972847459878[129] = 0;
   out_4550780972847459878[130] = 0;
   out_4550780972847459878[131] = 0;
   out_4550780972847459878[132] = 0;
   out_4550780972847459878[133] = 1;
   out_4550780972847459878[134] = 0;
   out_4550780972847459878[135] = 0;
   out_4550780972847459878[136] = 0;
   out_4550780972847459878[137] = 0;
   out_4550780972847459878[138] = 0;
   out_4550780972847459878[139] = 0;
   out_4550780972847459878[140] = 0;
   out_4550780972847459878[141] = 0;
   out_4550780972847459878[142] = 0;
   out_4550780972847459878[143] = 0;
   out_4550780972847459878[144] = 0;
   out_4550780972847459878[145] = 0;
   out_4550780972847459878[146] = 0;
   out_4550780972847459878[147] = 0;
   out_4550780972847459878[148] = 0;
   out_4550780972847459878[149] = 0;
   out_4550780972847459878[150] = 0;
   out_4550780972847459878[151] = 0;
   out_4550780972847459878[152] = 1;
   out_4550780972847459878[153] = 0;
   out_4550780972847459878[154] = 0;
   out_4550780972847459878[155] = 0;
   out_4550780972847459878[156] = 0;
   out_4550780972847459878[157] = 0;
   out_4550780972847459878[158] = 0;
   out_4550780972847459878[159] = 0;
   out_4550780972847459878[160] = 0;
   out_4550780972847459878[161] = 0;
   out_4550780972847459878[162] = 0;
   out_4550780972847459878[163] = 0;
   out_4550780972847459878[164] = 0;
   out_4550780972847459878[165] = 0;
   out_4550780972847459878[166] = 0;
   out_4550780972847459878[167] = 0;
   out_4550780972847459878[168] = 0;
   out_4550780972847459878[169] = 0;
   out_4550780972847459878[170] = 0;
   out_4550780972847459878[171] = 1;
   out_4550780972847459878[172] = 0;
   out_4550780972847459878[173] = 0;
   out_4550780972847459878[174] = 0;
   out_4550780972847459878[175] = 0;
   out_4550780972847459878[176] = 0;
   out_4550780972847459878[177] = 0;
   out_4550780972847459878[178] = 0;
   out_4550780972847459878[179] = 0;
   out_4550780972847459878[180] = 0;
   out_4550780972847459878[181] = 0;
   out_4550780972847459878[182] = 0;
   out_4550780972847459878[183] = 0;
   out_4550780972847459878[184] = 0;
   out_4550780972847459878[185] = 0;
   out_4550780972847459878[186] = 0;
   out_4550780972847459878[187] = 0;
   out_4550780972847459878[188] = 0;
   out_4550780972847459878[189] = 0;
   out_4550780972847459878[190] = 1;
   out_4550780972847459878[191] = 0;
   out_4550780972847459878[192] = 0;
   out_4550780972847459878[193] = 0;
   out_4550780972847459878[194] = 0;
   out_4550780972847459878[195] = 0;
   out_4550780972847459878[196] = 0;
   out_4550780972847459878[197] = 0;
   out_4550780972847459878[198] = 0;
   out_4550780972847459878[199] = 0;
   out_4550780972847459878[200] = 0;
   out_4550780972847459878[201] = 0;
   out_4550780972847459878[202] = 0;
   out_4550780972847459878[203] = 0;
   out_4550780972847459878[204] = 0;
   out_4550780972847459878[205] = 0;
   out_4550780972847459878[206] = 0;
   out_4550780972847459878[207] = 0;
   out_4550780972847459878[208] = 0;
   out_4550780972847459878[209] = 1;
   out_4550780972847459878[210] = 0;
   out_4550780972847459878[211] = 0;
   out_4550780972847459878[212] = 0;
   out_4550780972847459878[213] = 0;
   out_4550780972847459878[214] = 0;
   out_4550780972847459878[215] = 0;
   out_4550780972847459878[216] = 0;
   out_4550780972847459878[217] = 0;
   out_4550780972847459878[218] = 0;
   out_4550780972847459878[219] = 0;
   out_4550780972847459878[220] = 0;
   out_4550780972847459878[221] = 0;
   out_4550780972847459878[222] = 0;
   out_4550780972847459878[223] = 0;
   out_4550780972847459878[224] = 0;
   out_4550780972847459878[225] = 0;
   out_4550780972847459878[226] = 0;
   out_4550780972847459878[227] = 0;
   out_4550780972847459878[228] = 1;
   out_4550780972847459878[229] = 0;
   out_4550780972847459878[230] = 0;
   out_4550780972847459878[231] = 0;
   out_4550780972847459878[232] = 0;
   out_4550780972847459878[233] = 0;
   out_4550780972847459878[234] = 0;
   out_4550780972847459878[235] = 0;
   out_4550780972847459878[236] = 0;
   out_4550780972847459878[237] = 0;
   out_4550780972847459878[238] = 0;
   out_4550780972847459878[239] = 0;
   out_4550780972847459878[240] = 0;
   out_4550780972847459878[241] = 0;
   out_4550780972847459878[242] = 0;
   out_4550780972847459878[243] = 0;
   out_4550780972847459878[244] = 0;
   out_4550780972847459878[245] = 0;
   out_4550780972847459878[246] = 0;
   out_4550780972847459878[247] = 1;
   out_4550780972847459878[248] = 0;
   out_4550780972847459878[249] = 0;
   out_4550780972847459878[250] = 0;
   out_4550780972847459878[251] = 0;
   out_4550780972847459878[252] = 0;
   out_4550780972847459878[253] = 0;
   out_4550780972847459878[254] = 0;
   out_4550780972847459878[255] = 0;
   out_4550780972847459878[256] = 0;
   out_4550780972847459878[257] = 0;
   out_4550780972847459878[258] = 0;
   out_4550780972847459878[259] = 0;
   out_4550780972847459878[260] = 0;
   out_4550780972847459878[261] = 0;
   out_4550780972847459878[262] = 0;
   out_4550780972847459878[263] = 0;
   out_4550780972847459878[264] = 0;
   out_4550780972847459878[265] = 0;
   out_4550780972847459878[266] = 1;
   out_4550780972847459878[267] = 0;
   out_4550780972847459878[268] = 0;
   out_4550780972847459878[269] = 0;
   out_4550780972847459878[270] = 0;
   out_4550780972847459878[271] = 0;
   out_4550780972847459878[272] = 0;
   out_4550780972847459878[273] = 0;
   out_4550780972847459878[274] = 0;
   out_4550780972847459878[275] = 0;
   out_4550780972847459878[276] = 0;
   out_4550780972847459878[277] = 0;
   out_4550780972847459878[278] = 0;
   out_4550780972847459878[279] = 0;
   out_4550780972847459878[280] = 0;
   out_4550780972847459878[281] = 0;
   out_4550780972847459878[282] = 0;
   out_4550780972847459878[283] = 0;
   out_4550780972847459878[284] = 0;
   out_4550780972847459878[285] = 1;
   out_4550780972847459878[286] = 0;
   out_4550780972847459878[287] = 0;
   out_4550780972847459878[288] = 0;
   out_4550780972847459878[289] = 0;
   out_4550780972847459878[290] = 0;
   out_4550780972847459878[291] = 0;
   out_4550780972847459878[292] = 0;
   out_4550780972847459878[293] = 0;
   out_4550780972847459878[294] = 0;
   out_4550780972847459878[295] = 0;
   out_4550780972847459878[296] = 0;
   out_4550780972847459878[297] = 0;
   out_4550780972847459878[298] = 0;
   out_4550780972847459878[299] = 0;
   out_4550780972847459878[300] = 0;
   out_4550780972847459878[301] = 0;
   out_4550780972847459878[302] = 0;
   out_4550780972847459878[303] = 0;
   out_4550780972847459878[304] = 1;
   out_4550780972847459878[305] = 0;
   out_4550780972847459878[306] = 0;
   out_4550780972847459878[307] = 0;
   out_4550780972847459878[308] = 0;
   out_4550780972847459878[309] = 0;
   out_4550780972847459878[310] = 0;
   out_4550780972847459878[311] = 0;
   out_4550780972847459878[312] = 0;
   out_4550780972847459878[313] = 0;
   out_4550780972847459878[314] = 0;
   out_4550780972847459878[315] = 0;
   out_4550780972847459878[316] = 0;
   out_4550780972847459878[317] = 0;
   out_4550780972847459878[318] = 0;
   out_4550780972847459878[319] = 0;
   out_4550780972847459878[320] = 0;
   out_4550780972847459878[321] = 0;
   out_4550780972847459878[322] = 0;
   out_4550780972847459878[323] = 1;
}
void h_4(double *state, double *unused, double *out_8637530403510222813) {
   out_8637530403510222813[0] = state[6] + state[9];
   out_8637530403510222813[1] = state[7] + state[10];
   out_8637530403510222813[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_1204250909582981291) {
   out_1204250909582981291[0] = 0;
   out_1204250909582981291[1] = 0;
   out_1204250909582981291[2] = 0;
   out_1204250909582981291[3] = 0;
   out_1204250909582981291[4] = 0;
   out_1204250909582981291[5] = 0;
   out_1204250909582981291[6] = 1;
   out_1204250909582981291[7] = 0;
   out_1204250909582981291[8] = 0;
   out_1204250909582981291[9] = 1;
   out_1204250909582981291[10] = 0;
   out_1204250909582981291[11] = 0;
   out_1204250909582981291[12] = 0;
   out_1204250909582981291[13] = 0;
   out_1204250909582981291[14] = 0;
   out_1204250909582981291[15] = 0;
   out_1204250909582981291[16] = 0;
   out_1204250909582981291[17] = 0;
   out_1204250909582981291[18] = 0;
   out_1204250909582981291[19] = 0;
   out_1204250909582981291[20] = 0;
   out_1204250909582981291[21] = 0;
   out_1204250909582981291[22] = 0;
   out_1204250909582981291[23] = 0;
   out_1204250909582981291[24] = 0;
   out_1204250909582981291[25] = 1;
   out_1204250909582981291[26] = 0;
   out_1204250909582981291[27] = 0;
   out_1204250909582981291[28] = 1;
   out_1204250909582981291[29] = 0;
   out_1204250909582981291[30] = 0;
   out_1204250909582981291[31] = 0;
   out_1204250909582981291[32] = 0;
   out_1204250909582981291[33] = 0;
   out_1204250909582981291[34] = 0;
   out_1204250909582981291[35] = 0;
   out_1204250909582981291[36] = 0;
   out_1204250909582981291[37] = 0;
   out_1204250909582981291[38] = 0;
   out_1204250909582981291[39] = 0;
   out_1204250909582981291[40] = 0;
   out_1204250909582981291[41] = 0;
   out_1204250909582981291[42] = 0;
   out_1204250909582981291[43] = 0;
   out_1204250909582981291[44] = 1;
   out_1204250909582981291[45] = 0;
   out_1204250909582981291[46] = 0;
   out_1204250909582981291[47] = 1;
   out_1204250909582981291[48] = 0;
   out_1204250909582981291[49] = 0;
   out_1204250909582981291[50] = 0;
   out_1204250909582981291[51] = 0;
   out_1204250909582981291[52] = 0;
   out_1204250909582981291[53] = 0;
}
void h_10(double *state, double *unused, double *out_408371076255569127) {
   out_408371076255569127[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_408371076255569127[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_408371076255569127[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_669486987569912933) {
   out_669486987569912933[0] = 0;
   out_669486987569912933[1] = 9.8100000000000005*cos(state[1]);
   out_669486987569912933[2] = 0;
   out_669486987569912933[3] = 0;
   out_669486987569912933[4] = -state[8];
   out_669486987569912933[5] = state[7];
   out_669486987569912933[6] = 0;
   out_669486987569912933[7] = state[5];
   out_669486987569912933[8] = -state[4];
   out_669486987569912933[9] = 0;
   out_669486987569912933[10] = 0;
   out_669486987569912933[11] = 0;
   out_669486987569912933[12] = 1;
   out_669486987569912933[13] = 0;
   out_669486987569912933[14] = 0;
   out_669486987569912933[15] = 1;
   out_669486987569912933[16] = 0;
   out_669486987569912933[17] = 0;
   out_669486987569912933[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_669486987569912933[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_669486987569912933[20] = 0;
   out_669486987569912933[21] = state[8];
   out_669486987569912933[22] = 0;
   out_669486987569912933[23] = -state[6];
   out_669486987569912933[24] = -state[5];
   out_669486987569912933[25] = 0;
   out_669486987569912933[26] = state[3];
   out_669486987569912933[27] = 0;
   out_669486987569912933[28] = 0;
   out_669486987569912933[29] = 0;
   out_669486987569912933[30] = 0;
   out_669486987569912933[31] = 1;
   out_669486987569912933[32] = 0;
   out_669486987569912933[33] = 0;
   out_669486987569912933[34] = 1;
   out_669486987569912933[35] = 0;
   out_669486987569912933[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_669486987569912933[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_669486987569912933[38] = 0;
   out_669486987569912933[39] = -state[7];
   out_669486987569912933[40] = state[6];
   out_669486987569912933[41] = 0;
   out_669486987569912933[42] = state[4];
   out_669486987569912933[43] = -state[3];
   out_669486987569912933[44] = 0;
   out_669486987569912933[45] = 0;
   out_669486987569912933[46] = 0;
   out_669486987569912933[47] = 0;
   out_669486987569912933[48] = 0;
   out_669486987569912933[49] = 0;
   out_669486987569912933[50] = 1;
   out_669486987569912933[51] = 0;
   out_669486987569912933[52] = 0;
   out_669486987569912933[53] = 1;
}
void h_13(double *state, double *unused, double *out_2633952316633081407) {
   out_2633952316633081407[0] = state[3];
   out_2633952316633081407[1] = state[4];
   out_2633952316633081407[2] = state[5];
}
void H_13(double *state, double *unused, double *out_4416524734915314092) {
   out_4416524734915314092[0] = 0;
   out_4416524734915314092[1] = 0;
   out_4416524734915314092[2] = 0;
   out_4416524734915314092[3] = 1;
   out_4416524734915314092[4] = 0;
   out_4416524734915314092[5] = 0;
   out_4416524734915314092[6] = 0;
   out_4416524734915314092[7] = 0;
   out_4416524734915314092[8] = 0;
   out_4416524734915314092[9] = 0;
   out_4416524734915314092[10] = 0;
   out_4416524734915314092[11] = 0;
   out_4416524734915314092[12] = 0;
   out_4416524734915314092[13] = 0;
   out_4416524734915314092[14] = 0;
   out_4416524734915314092[15] = 0;
   out_4416524734915314092[16] = 0;
   out_4416524734915314092[17] = 0;
   out_4416524734915314092[18] = 0;
   out_4416524734915314092[19] = 0;
   out_4416524734915314092[20] = 0;
   out_4416524734915314092[21] = 0;
   out_4416524734915314092[22] = 1;
   out_4416524734915314092[23] = 0;
   out_4416524734915314092[24] = 0;
   out_4416524734915314092[25] = 0;
   out_4416524734915314092[26] = 0;
   out_4416524734915314092[27] = 0;
   out_4416524734915314092[28] = 0;
   out_4416524734915314092[29] = 0;
   out_4416524734915314092[30] = 0;
   out_4416524734915314092[31] = 0;
   out_4416524734915314092[32] = 0;
   out_4416524734915314092[33] = 0;
   out_4416524734915314092[34] = 0;
   out_4416524734915314092[35] = 0;
   out_4416524734915314092[36] = 0;
   out_4416524734915314092[37] = 0;
   out_4416524734915314092[38] = 0;
   out_4416524734915314092[39] = 0;
   out_4416524734915314092[40] = 0;
   out_4416524734915314092[41] = 1;
   out_4416524734915314092[42] = 0;
   out_4416524734915314092[43] = 0;
   out_4416524734915314092[44] = 0;
   out_4416524734915314092[45] = 0;
   out_4416524734915314092[46] = 0;
   out_4416524734915314092[47] = 0;
   out_4416524734915314092[48] = 0;
   out_4416524734915314092[49] = 0;
   out_4416524734915314092[50] = 0;
   out_4416524734915314092[51] = 0;
   out_4416524734915314092[52] = 0;
   out_4416524734915314092[53] = 0;
}
void h_14(double *state, double *unused, double *out_5630345490908546158) {
   out_5630345490908546158[0] = state[6];
   out_5630345490908546158[1] = state[7];
   out_5630345490908546158[2] = state[8];
}
void H_14(double *state, double *unused, double *out_5167491765922465820) {
   out_5167491765922465820[0] = 0;
   out_5167491765922465820[1] = 0;
   out_5167491765922465820[2] = 0;
   out_5167491765922465820[3] = 0;
   out_5167491765922465820[4] = 0;
   out_5167491765922465820[5] = 0;
   out_5167491765922465820[6] = 1;
   out_5167491765922465820[7] = 0;
   out_5167491765922465820[8] = 0;
   out_5167491765922465820[9] = 0;
   out_5167491765922465820[10] = 0;
   out_5167491765922465820[11] = 0;
   out_5167491765922465820[12] = 0;
   out_5167491765922465820[13] = 0;
   out_5167491765922465820[14] = 0;
   out_5167491765922465820[15] = 0;
   out_5167491765922465820[16] = 0;
   out_5167491765922465820[17] = 0;
   out_5167491765922465820[18] = 0;
   out_5167491765922465820[19] = 0;
   out_5167491765922465820[20] = 0;
   out_5167491765922465820[21] = 0;
   out_5167491765922465820[22] = 0;
   out_5167491765922465820[23] = 0;
   out_5167491765922465820[24] = 0;
   out_5167491765922465820[25] = 1;
   out_5167491765922465820[26] = 0;
   out_5167491765922465820[27] = 0;
   out_5167491765922465820[28] = 0;
   out_5167491765922465820[29] = 0;
   out_5167491765922465820[30] = 0;
   out_5167491765922465820[31] = 0;
   out_5167491765922465820[32] = 0;
   out_5167491765922465820[33] = 0;
   out_5167491765922465820[34] = 0;
   out_5167491765922465820[35] = 0;
   out_5167491765922465820[36] = 0;
   out_5167491765922465820[37] = 0;
   out_5167491765922465820[38] = 0;
   out_5167491765922465820[39] = 0;
   out_5167491765922465820[40] = 0;
   out_5167491765922465820[41] = 0;
   out_5167491765922465820[42] = 0;
   out_5167491765922465820[43] = 0;
   out_5167491765922465820[44] = 1;
   out_5167491765922465820[45] = 0;
   out_5167491765922465820[46] = 0;
   out_5167491765922465820[47] = 0;
   out_5167491765922465820[48] = 0;
   out_5167491765922465820[49] = 0;
   out_5167491765922465820[50] = 0;
   out_5167491765922465820[51] = 0;
   out_5167491765922465820[52] = 0;
   out_5167491765922465820[53] = 0;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_4, H_4, NULL, in_z, in_R, in_ea, MAHA_THRESH_4);
}
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_10, H_10, NULL, in_z, in_R, in_ea, MAHA_THRESH_10);
}
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_13, H_13, NULL, in_z, in_R, in_ea, MAHA_THRESH_13);
}
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_14, H_14, NULL, in_z, in_R, in_ea, MAHA_THRESH_14);
}
void pose_err_fun(double *nom_x, double *delta_x, double *out_5615908840917548007) {
  err_fun(nom_x, delta_x, out_5615908840917548007);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_3325133064770946759) {
  inv_err_fun(nom_x, true_x, out_3325133064770946759);
}
void pose_H_mod_fun(double *state, double *out_5724271770107739515) {
  H_mod_fun(state, out_5724271770107739515);
}
void pose_f_fun(double *state, double dt, double *out_6512085752749911959) {
  f_fun(state,  dt, out_6512085752749911959);
}
void pose_F_fun(double *state, double dt, double *out_4550780972847459878) {
  F_fun(state,  dt, out_4550780972847459878);
}
void pose_h_4(double *state, double *unused, double *out_8637530403510222813) {
  h_4(state, unused, out_8637530403510222813);
}
void pose_H_4(double *state, double *unused, double *out_1204250909582981291) {
  H_4(state, unused, out_1204250909582981291);
}
void pose_h_10(double *state, double *unused, double *out_408371076255569127) {
  h_10(state, unused, out_408371076255569127);
}
void pose_H_10(double *state, double *unused, double *out_669486987569912933) {
  H_10(state, unused, out_669486987569912933);
}
void pose_h_13(double *state, double *unused, double *out_2633952316633081407) {
  h_13(state, unused, out_2633952316633081407);
}
void pose_H_13(double *state, double *unused, double *out_4416524734915314092) {
  H_13(state, unused, out_4416524734915314092);
}
void pose_h_14(double *state, double *unused, double *out_5630345490908546158) {
  h_14(state, unused, out_5630345490908546158);
}
void pose_H_14(double *state, double *unused, double *out_5167491765922465820) {
  H_14(state, unused, out_5167491765922465820);
}
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
}

const EKF pose = {
  .name = "pose",
  .kinds = { 4, 10, 13, 14 },
  .feature_kinds = {  },
  .f_fun = pose_f_fun,
  .F_fun = pose_F_fun,
  .err_fun = pose_err_fun,
  .inv_err_fun = pose_inv_err_fun,
  .H_mod_fun = pose_H_mod_fun,
  .predict = pose_predict,
  .hs = {
    { 4, pose_h_4 },
    { 10, pose_h_10 },
    { 13, pose_h_13 },
    { 14, pose_h_14 },
  },
  .Hs = {
    { 4, pose_H_4 },
    { 10, pose_H_10 },
    { 13, pose_H_13 },
    { 14, pose_H_14 },
  },
  .updates = {
    { 4, pose_update_4 },
    { 10, pose_update_10 },
    { 13, pose_update_13 },
    { 14, pose_update_14 },
  },
  .Hes = {
  },
  .sets = {
  },
  .extra_routines = {
  },
};

ekf_lib_init(pose)
