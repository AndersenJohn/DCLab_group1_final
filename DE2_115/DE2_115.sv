module DE2_115 (
	input CLOCK_50,
	input CLOCK2_50,
	input CLOCK3_50,
	input ENETCLK_25,
	input SMA_CLKIN,
	output SMA_CLKOUT,
	output [8:0] LEDG,
	output [17:0] LEDR,
	input [3:0] KEY,
	input [17:0] SW,
	output [6:0] HEX0,
	output [6:0] HEX1,
	output [6:0] HEX2,
	output [6:0] HEX3,
	output [6:0] HEX4,
	output [6:0] HEX5,
	output [6:0] HEX6,
	output [6:0] HEX7,
	output LCD_BLON,
	inout [7:0] LCD_DATA,
	output LCD_EN,
	output LCD_ON,
	output LCD_RS,
	output LCD_RW,
	output UART_CTS,
	input UART_RTS,
	input UART_RXD,
	output UART_TXD,
	inout PS2_CLK,
	inout PS2_DAT,
	inout PS2_CLK2,
	inout PS2_DAT2,
	output SD_CLK,
	inout SD_CMD,
	inout [3:0] SD_DAT,
	input SD_WP_N,
	output [7:0] VGA_B,
	output VGA_BLANK_N,
	output VGA_CLK,
	output [7:0] VGA_G,
	output VGA_HS,
	output [7:0] VGA_R,
	output VGA_SYNC_N,
	output VGA_VS,
	input AUD_ADCDAT,
	inout AUD_ADCLRCK,
	inout AUD_BCLK,
	output AUD_DACDAT,
	inout AUD_DACLRCK,
	output AUD_XCK,
	output EEP_I2C_SCLK,
	inout EEP_I2C_SDAT,
	output I2C_SCLK,
	inout I2C_SDAT,
	output ENET0_GTX_CLK,
	input ENET0_INT_N,
	output ENET0_MDC,
	input ENET0_MDIO,
	output ENET0_RST_N,
	input ENET0_RX_CLK,
	input ENET0_RX_COL,
	input ENET0_RX_CRS,
	input [3:0] ENET0_RX_DATA,
	input ENET0_RX_DV,
	input ENET0_RX_ER,
	input ENET0_TX_CLK,
	output [3:0] ENET0_TX_DATA,
	output ENET0_TX_EN,
	output ENET0_TX_ER,
	input ENET0_LINK100,
	output ENET1_GTX_CLK,
	input ENET1_INT_N,
	output ENET1_MDC,
	input ENET1_MDIO,
	output ENET1_RST_N,
	input ENET1_RX_CLK,
	input ENET1_RX_COL,
	input ENET1_RX_CRS,
	input [3:0] ENET1_RX_DATA,
	input ENET1_RX_DV,
	input ENET1_RX_ER,
	input ENET1_TX_CLK,
	output [3:0] ENET1_TX_DATA,
	output ENET1_TX_EN,
	output ENET1_TX_ER,
	input ENET1_LINK100,
	input TD_CLK27,
	input [7:0] TD_DATA,
	input TD_HS,
	output TD_RESET_N,
	input TD_VS,
	inout [15:0] OTG_DATA,
	output [1:0] OTG_ADDR,
	output OTG_CS_N,
	output OTG_WR_N,
	output OTG_RD_N,
	input OTG_INT,
	output OTG_RST_N,
	input IRDA_RXD,
	output [12:0] DRAM_ADDR,
	output [1:0] DRAM_BA,
	output DRAM_CAS_N,
	output DRAM_CKE,
	output DRAM_CLK,
	output DRAM_CS_N,
	inout [31:0] DRAM_DQ,
	output [3:0] DRAM_DQM,
	output DRAM_RAS_N,
	output DRAM_WE_N,
	output [19:0] SRAM_ADDR,
	output SRAM_CE_N,
	inout [15:0] SRAM_DQ,
	output SRAM_LB_N,
	output SRAM_OE_N,
	output SRAM_UB_N,
	output SRAM_WE_N,
	output [22:0] FL_ADDR,
	output FL_CE_N,
	inout [7:0] FL_DQ,
	output FL_OE_N,
	output FL_RST_N,
	input FL_RY,
	output FL_WE_N,
	output FL_WP_N,
	inout [35:0] GPIO,
	input HSMC_CLKIN_P1,
	input HSMC_CLKIN_P2,
	input HSMC_CLKIN0,
	output HSMC_CLKOUT_P1,
	output HSMC_CLKOUT_P2,
	output HSMC_CLKOUT0,
	inout [3:0] HSMC_D,
	input [16:0] HSMC_RX_D_P,
	output [16:0] HSMC_TX_D_P,
	inout [6:0] EX_IO
);

// Clock and Reset Signals
logic  i_clk;
assign i_clk = CLOCK_50;
logic  i_rst_n, i_start;
assign i_rst_n = KEY[0];
assign i_start = ~KEY[1];

// bullet num initial wires from Game_logic
logic [3:0] bullet_num_initial0;
logic [3:0] bullet_num_initial1;
logic [3:0] bullet_num_initial2;
logic [3:0] bullet_num_initial3;

SevenHexDecoder bulletnum0 (
	.i_hex(bullet_num_initial0),
	.o_seven_one(HEX0)
);	
SevenHexDecoder bulletnum1 (
	.i_hex(bullet_num_initial1),
	.o_seven_one(HEX1)
);
SevenHexDecoder bulletnum2 (
	.i_hex(bullet_num_initial2),
	.o_seven_one(HEX2)
);
SevenHexDecoder bulletnum3 (
	.i_hex(bullet_num_initial3),
	.o_seven_one(HEX3)
);

// // Sparkle Signal & 47Hz Square Wave Signal
logic sparkle;
logic o_47Hz_sqrwave;
Light_Gen Light_Gen_inst (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.o_on(sparkle),
	.o_47Hz_sqrwave(o_47Hz_sqrwave)
);

// Player Signals
logic playerA, playerB;
logic start_ai_p0, start_ai_p1;

logic [3:0] action;
logic [3:0] action_p0, action_p1;
assign action = (playerA) ? action_p1 : action_p0;

// Player Type Selection Signals
// 0: player, 1: AI  
logic p0_player, p1_player;                                                                                                                                                 
assign p0_player = SW[0];
assign p1_player = SW[1];

// Item Shoot Input
// Magnetic Sensor Inputs
logic       i_item_shoot;
logic       item_shoot_ai, item_shoot_player;
logic       item_shoot_player_gated;
logic 	  	gpio_12_db;
assign GPIO[12]	= 1'bz;
Debounce #(
	.CNT_N(1000000)
) debounce_item_shoot (
	.i_in(GPIO[12]),
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.o_debounced(),
	.o_neg(),
	.o_pos(gpio_12_db)
);
Magnetic_Reed_Switch_Proc item_shoot (
	.i_clk(i_clk),	
	.i_rst_n(i_rst_n),
	.i_switch(gpio_12_db),
	.o_switch(item_shoot_player)
);
assign i_item_shoot = ((playerA && p1_player) || (!playerA && p0_player)) ? item_shoot_ai : item_shoot_player_gated;

// Trigger & Shock Signals
logic trigger_button, trigger_shock_halfsecond;
logic shock_signal; // 扣寫的時候 pull-up 一陣子 (電擊持續時間)
assign GPIO[14] = 1'bz;
Trigger_Debounce debounce_trigger (
	.i_in(GPIO[14]),
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.o_trigger(trigger_button)
);
assign GPIO[13] = trigger_shock_halfsecond;
// Shoot Trigger Input
// Button Input
logic       i_shoot_trigger;
logic       shoot_trigger_ai;
logic       trigger_button_gated;
assign i_shoot_trigger = ((playerA && p1_player) || (!playerA && p0_player)) ? shoot_trigger_ai : trigger_button_gated; // Active Low
Trigger_Shock_Counter Trigger_Shock_Counter_inst (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_shock(shock_signal),
	.o_trigger_shock_halfsecond(trigger_shock_halfsecond)
);

// Item Select Inputs
// Button Inputs
// GPIO[2], GPIO[4], GPIO[6], GPIO[8], GPIO[10], GPIO[0] for Player 0
// GPIO[26], GPIO[28], GPIO[30], GPIO[32], GPIO[34], GPIO[24] for Player 1
logic [5:0] i_item_select;
logic [5:0] item_select_ai;
logic [5:0] item_select_player0, item_select_player1;
logic [5:0] item_select_player0_gated, item_select_player1_gated;
assign i_item_select = ((playerA && p1_player) || (!playerA && p0_player)) ? item_select_ai : (!playerA) ? item_select_player0_gated : item_select_player1_gated;

// Shoot Select Input
// Button Input
// GPIO[16], GPIO[17] for Shoot Select p0 / GPIO[18], GPIO[19] for Shoot Select p1
// Assign trigger for SW[17] temporarily
logic       i_shoot_select;
logic       shoot_select_ai, shoot_select_player;
assign GPIO[16] = 1'bz;
assign GPIO[18] = 1'bz;
// Invert 16 and 18 for active low input
Shoot_Sel_Switch switch (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_playerA(playerA),
	.i_to_p0(~GPIO[18]),
	.i_to_p1(~GPIO[16]),
	.i_trigger(i_shoot_trigger),
	.i_sparkle(sparkle),
	.o_to_p0(GPIO[19]),
	.o_to_p1(GPIO[17]),
	.o_shoot_select(shoot_select_player)
);
assign i_shoot_select = ((playerA && p1_player) || (!playerA && p0_player)) ? shoot_select_ai : shoot_select_player;

// Game Logic Signals
logic [2:0] o_hp_p0;
logic [2:0] o_hp_p1;
logic [3:0] o_bullet_bitmap_ptr;
logic [3:0] o_total_bullet;
logic [3:0] o_total_bullet_remaining;
logic [2:0] o_bullet_filled;
logic [2:0] o_bullet_empty;
logic       o_bullet_report_valid;
logic       o_bullet_report;
logic [2:0] o_report_idx;
logic [1:0] o_winner;     

logic [3:0] item_column_p0 [0:5];
logic [3:0] item_column_p1 [0:5];

logic [3:0] state;

logic [2:0] item_number0_p0, item_number1_p0, item_number2_p0, item_number3_p0, item_number4_p0, item_number5_p0, item_number6_p0;
logic [2:0] item_number0_p1, item_number1_p1, item_number2_p1, item_number3_p1, item_number4_p1, item_number5_p1, item_number6_p1;

logic phase_item, phase_shoot;
assign phase_item = (state == 4'd2 || state == 4'd3) ? 1'b1 : 1'b0;
assign phase_shoot = (state == 4'd5 || state == 4'd6) ? 1'b1 : 1'b0;

logic [7:0] bullet_bitmap;
logic [1:0] bullet_bitmap_p0 [0:7];
logic [1:0] bullet_bitmap_p1 [0:7];

logic o_saw_active, o_reverse_active, o_handcuff_active;


logic [3:0] item_column [0:5];


//uart tx signals
logic       w_tx_busy;
logic       w_tx_start;
logic [7:0] w_tx_data;
logic       w_tx_done;


genvar i;
generate
    for (i = 0; i < 6; i = i + 1) begin : ITEM_COLUMN_MUX
        assign item_column[i] = (playerA) ? item_column_p1[i] : item_column_p0[i];
    end
endgenerate

// Global Lockout / Cooldown Logic
logic [25:0] lockout_cnt; // Increased bit width for 50M
logic lockout_active;

// Trigger on raw player inputs
logic player_action_detected;
assign player_action_detected = item_shoot_player || (|item_select_player0) || (|item_select_player1) || trigger_button;

always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        lockout_cnt <= 26'd0;
    end else begin
        if (lockout_cnt > 0) begin
            lockout_cnt <= lockout_cnt - 1'b1;
        end else if (player_action_detected) begin
            lockout_cnt <= 26'd25000000; // 0.5s at 50MHz
        end
    end
end

assign lockout_active = (lockout_cnt > 0);

// Gate the player inputs
assign item_shoot_player_gated = lockout_active ? 1'b0 : item_shoot_player;
assign trigger_button_gated = lockout_active ? 1'b0 : trigger_button;
assign item_select_player0_gated = lockout_active ? 6'd0 : item_select_player0;
assign item_select_player1_gated = lockout_active ? 6'd0 : item_select_player1;


Game_logic Game_logic_inst(
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_start(i_start),
	.i_uart_done(w_tx_done),
	.i_item_shoot(i_item_shoot),
	.i_item_select(i_item_select),
	.i_shoot_trigger(i_shoot_trigger),
	.i_shoot_select(i_shoot_select),
	.o_hp_p0(o_hp_p0),
	.o_hp_p1(o_hp_p1),
	.o_bullet_bitmap_ptr(o_bullet_bitmap_ptr),
	.o_total_bullet(o_total_bullet),
	.o_total_bullet_remaining(o_total_bullet_remaining),
	.o_bullet_filled(o_bullet_filled),
	.o_bullet_empty(o_bullet_empty),
	.o_bullet_report_valid(o_bullet_report_valid),
	.o_bullet_report(o_bullet_report),
	.o_report_idx(o_report_idx),
	.o_winner(o_winner),
	.o_item_column_p0_0(item_column_p0[0]),
	.o_item_column_p0_1(item_column_p0[1]),
	.o_item_column_p0_2(item_column_p0[2]),
	.o_item_column_p0_3(item_column_p0[3]),
	.o_item_column_p0_4(item_column_p0[4]),
	.o_item_column_p0_5(item_column_p0[5]),
	.o_item_column_p1_0(item_column_p1[0]),
	.o_item_column_p1_1(item_column_p1[1]),
	.o_item_column_p1_2(item_column_p1[2]),
	.o_item_column_p1_3(item_column_p1[3]),
	.o_item_column_p1_4(item_column_p1[4]),
	.o_item_column_p1_5(item_column_p1[5]),
	.o_state(state),
	.o_playerA(playerA),
	.o_playerB(playerB),
	.o_bullet_bitmap(bullet_bitmap),
	.o_saw_active(o_saw_active),
	.o_reverse_active(o_reverse_active),
	.o_handcuff_active(o_handcuff_active),
	.o_shock(shock_signal),
	.o_bullet_num_initial0(bullet_num_initial0),
	.o_bullet_num_initial1(bullet_num_initial1),
	.o_bullet_num_initial2(bullet_num_initial2),
	.o_bullet_num_initial3(bullet_num_initial3)
);

Game_PC_Interface Game_PC_Interface_inst (
	.clk(i_clk),
	.rst_n(i_rst_n),
	.i_winner(o_winner),
	.i_state(state),
	.i_playerA(playerA),
	.i_playerB(playerB),
	.i_saw_active(o_saw_active),
	.i_reverse_active(o_reverse_active),
	.i_handcuff_active(o_handcuff_active),
	.i_bullet_report_valid(o_bullet_report_valid),
	.i_bullet_report(o_bullet_report),
	.i_report_idx(o_report_idx),
	.i_hp_p0(o_hp_p0),
	.i_hp_p1(o_hp_p1),
	.i_total_bullet(o_total_bullet),
	.i_total_bullet_remaining(o_total_bullet_remaining),
	.i_bullet_filled(o_bullet_filled),
	.i_bullet_empty(o_bullet_empty),
	.i_bullet_bitmap_ptr(o_bullet_bitmap_ptr),
	.i_bullet_bitmap(bullet_bitmap),
	.i_item_column_p0_0(item_column_p0[0]),
	.i_item_column_p0_1(item_column_p0[1]),
	.i_item_column_p0_2(item_column_p0[2]),
	.i_item_column_p0_3(item_column_p0[3]),
	.i_item_column_p0_4(item_column_p0[4]),
	.i_item_column_p0_5(item_column_p0[5]),
	.i_item_column_p1_0(item_column_p1[0]),
	.i_item_column_p1_1(item_column_p1[1]),
	.i_item_column_p1_2(item_column_p1[2]),
	.i_item_column_p1_3(item_column_p1[3]),
	.i_item_column_p1_4(item_column_p1[4]),
	.i_item_column_p1_5(item_column_p1[5]),
	.o_tx_data(w_tx_data),
	.o_tx_start(w_tx_start),
	.i_tx_busy(w_tx_busy),
	.o_tx_done(w_tx_done)
);

uart_tx uart_tx_inst (
	.clk(i_clk),
	.rst_n(i_rst_n),
	.tx_start(w_tx_start), 
	.tx_data(w_tx_data), 
	.tx_line(UART_TXD),
	.tx_busy(w_tx_busy) 
);


Encoder_to_AI #(.AI_Player(0)) encoder_p0 (
	.clk(i_clk),
	.rst_n(i_rst_n),
	.hp_p0(o_hp_p0),
	.hp_p1(o_hp_p1),
	.bullet_bitmap_ptr(o_bullet_bitmap_ptr),
	.total_bullet(o_total_bullet),
	.total_bullet_remaining(o_total_bullet_remaining),
	.bullet_report_valid(o_bullet_report_valid),
	.bullet_report(o_bullet_report),
	.report_idx(o_report_idx),
	.item0_p0(item_column_p0[0]),
	.item1_p0(item_column_p0[1]),
	.item2_p0(item_column_p0[2]),
	.item3_p0(item_column_p0[3]),
	.item4_p0(item_column_p0[4]),
	.item5_p0(item_column_p0[5]),
	.item0_p1(item_column_p1[0]),
	.item1_p1(item_column_p1[1]),
	.item2_p1(item_column_p1[2]),
	.item3_p1(item_column_p1[3]),
	.item4_p1(item_column_p1[4]),
	.item5_p1(item_column_p1[5]),
	.state(state),
	.playerA(playerA),
	.playerB(playerB),
	.bullet_bitmap(bullet_bitmap),
	.o_item_number0_p0(item_number0_p0),
	.o_item_number1_p0(item_number1_p0),
	.o_item_number2_p0(item_number2_p0),
	.o_item_number3_p0(item_number3_p0),
	.o_item_number4_p0(item_number4_p0),
	.o_item_number5_p0(item_number5_p0),
	.o_item_number6_p0(item_number6_p0),
	//.o_item_number0_p1(item_number0_p1),
	//.o_item_number1_p1(item_number1_p1),
	//.o_item_number2_p1(item_number2_p1),
	//.o_item_number3_p1(item_number3_p1),
	//.o_item_number4_p1(item_number4_p1),
	//.o_item_number5_p1(item_number5_p1),
	//.o_item_number6_p1(item_number6_p1),
	//.o_phase_item(phase_item),
	//.o_phase_shoot(phase_shoot),
	.bullet_bitmap_p0_0(bullet_bitmap_p0[0]),
	.bullet_bitmap_p0_1(bullet_bitmap_p0[1]),
	.bullet_bitmap_p0_2(bullet_bitmap_p0[2]),
	.bullet_bitmap_p0_3(bullet_bitmap_p0[3]),
	.bullet_bitmap_p0_4(bullet_bitmap_p0[4]),
	.bullet_bitmap_p0_5(bullet_bitmap_p0[5]),
	.bullet_bitmap_p0_6(bullet_bitmap_p0[6]),
	.bullet_bitmap_p0_7(bullet_bitmap_p0[7]),
	//.bullet_bitmap_p1_0(bullet_bitmap_p1[0]),
	//.bullet_bitmap_p1_1(bullet_bitmap_p1[1]),
	//.bullet_bitmap_p1_2(bullet_bitmap_p1[2]),
	//.bullet_bitmap_p1_3(bullet_bitmap_p1[3]),
	//.bullet_bitmap_p1_4(bullet_bitmap_p1[4]),
	//.bullet_bitmap_p1_5(bullet_bitmap_p1[5]),
	//.bullet_bitmap_p1_6(bullet_bitmap_p1[6]),
	//.bullet_bitmap_p1_7(bullet_bitmap_p1[7]),
	.o_start(start_ai_p0)
);

Encoder_to_AI #(.AI_Player(1)) encoder_p1 (
	.clk(i_clk),
	.rst_n(i_rst_n),
	.hp_p0(o_hp_p0),
	.hp_p1(o_hp_p1),
	.bullet_bitmap_ptr(o_bullet_bitmap_ptr),
	.total_bullet(o_total_bullet),
	.total_bullet_remaining(o_total_bullet_remaining),
	.bullet_report_valid(o_bullet_report_valid),
	.bullet_report(o_bullet_report),
	.report_idx(o_report_idx),
	.item0_p0(item_column_p0[0]),
	.item1_p0(item_column_p0[1]),
	.item2_p0(item_column_p0[2]),
	.item3_p0(item_column_p0[3]),
	.item4_p0(item_column_p0[4]),
	.item5_p0(item_column_p0[5]),
	.item0_p1(item_column_p1[0]),
	.item1_p1(item_column_p1[1]),
	.item2_p1(item_column_p1[2]),
	.item3_p1(item_column_p1[3]),
	.item4_p1(item_column_p1[4]),
	.item5_p1(item_column_p1[5]),
	.state(state),
	.playerA(playerA),
	.playerB(playerB),
	.bullet_bitmap(bullet_bitmap),
	//.o_item_number0_p0(item_number0_p0),
	//.o_item_number1_p0(item_number1_p0),
	//.o_item_number2_p0(item_number2_p0),
	//.o_item_number3_p0(item_number3_p0),
	//.o_item_number4_p0(item_number4_p0),
	//.o_item_number5_p0(item_number5_p0),
	//.o_item_number6_p0(item_number6_p0),
	.o_item_number0_p1(item_number0_p1),
	.o_item_number1_p1(item_number1_p1),
	.o_item_number2_p1(item_number2_p1),
	.o_item_number3_p1(item_number3_p1),
	.o_item_number4_p1(item_number4_p1),
	.o_item_number5_p1(item_number5_p1),
	.o_item_number6_p1(item_number6_p1),
	//.o_phase_item(phase_item),
	//.o_phase_shoot(phase_shoot),
	//.bullet_bitmap_p0_0(bullet_bitmap_p0[0]),
	//.bullet_bitmap_p0_1(bullet_bitmap_p0[1]),
	//.bullet_bitmap_p0_2(bullet_bitmap_p0[2]),
	//.bullet_bitmap_p0_3(bullet_bitmap_p0[3]),
	//.bullet_bitmap_p0_4(bullet_bitmap_p0[4]),
	//.bullet_bitmap_p0_5(bullet_bitmap_p0[5]),
	//.bullet_bitmap_p0_6(bullet_bitmap_p0[6]),
	//.bullet_bitmap_p0_7(bullet_bitmap_p0[7]),
	.bullet_bitmap_p1_0(bullet_bitmap_p1[0]),
	.bullet_bitmap_p1_1(bullet_bitmap_p1[1]),
	.bullet_bitmap_p1_2(bullet_bitmap_p1[2]),
	.bullet_bitmap_p1_3(bullet_bitmap_p1[3]),
	.bullet_bitmap_p1_4(bullet_bitmap_p1[4]),
	.bullet_bitmap_p1_5(bullet_bitmap_p1[5]),
	.bullet_bitmap_p1_6(bullet_bitmap_p1[6]),
	.bullet_bitmap_p1_7(bullet_bitmap_p1[7]),
	.o_start(start_ai_p1)
);

AI_to_Top ai_to_top_inst (
	.clk(i_clk),
	.rst_n(i_rst_n),
	.action(action),
	.item_column0(item_column[0]),
	.item_column1(item_column[1]),
	.item_column2(item_column[2]),
	.item_column3(item_column[3]),
	.item_column4(item_column[4]),
	.item_column5(item_column[5]),
	.o_item_select(item_select_ai),
	.o_item_shoot(item_shoot_ai),
	.o_shoot_trigger(shoot_trigger_ai),
	.o_shoot_select(shoot_select_ai)
);

// 宣告給 RL_model 的輸入陣列
logic signed [15:0] p0_in_vec [0:32];
logic signed [15:0] p1_in_vec [0:32];

assign p0_in_vec = '{
	{3'b0, o_bullet_filled,10'b0},
	{3'b0, o_bullet_empty,10'b0},
	{2'b0, o_bullet_bitmap_ptr,10'b0},
	{5'b0, o_saw_active,10'b0},
	{5'b0, o_reverse_active,10'b0},
	{5'b0, phase_item,10'b0},
	{5'b0, phase_shoot,10'b0},
	{3'b0, o_hp_p0,10'b0},
	{5'b0, {o_handcuff_active & playerA},10'b0}, // o_handcuff_active & playerA 
	{3'b0, item_number0_p0,10'b0},
	{3'b0, item_number1_p0,10'b0},
	{3'b0, item_number2_p0,10'b0},
	{3'b0, item_number3_p0,10'b0},
	{3'b0, item_number4_p0,10'b0},
	{3'b0, item_number5_p0,10'b0},
	{3'b0, item_number6_p0,10'b0},
	{3'b0, o_hp_p1,10'b0},
	{5'b0, {o_handcuff_active & playerB},10'b0}, // o_handcuff_active & playerA 
	{3'b0, item_number0_p1,10'b0},
	{3'b0, item_number1_p1,10'b0},
	{3'b0, item_number2_p1,10'b0},
	{3'b0, item_number3_p1,10'b0},
	{3'b0, item_number4_p1,10'b0},
	{3'b0, item_number5_p1,10'b0},
	{3'b0, item_number6_p1,10'b0},
	{4'b0, bullet_bitmap_p0[0],10'b0},
	{4'b0, bullet_bitmap_p0[1],10'b0},
	{4'b0, bullet_bitmap_p0[2],10'b0},
	{4'b0, bullet_bitmap_p0[3],10'b0},
	{4'b0, bullet_bitmap_p0[4],10'b0},
	{4'b0, bullet_bitmap_p0[5],10'b0},
	{4'b0, bullet_bitmap_p0[6],10'b0},
	{4'b0, bullet_bitmap_p0[7],10'b0}
};
assign p1_in_vec = '{
	{3'b0, o_bullet_filled,10'b0},
	{3'b0, o_bullet_empty,10'b0},
	{2'b0, o_bullet_bitmap_ptr,10'b0},
	{5'b0, o_saw_active,10'b0},
	{5'b0, o_reverse_active,10'b0},
	{5'b0, phase_item,10'b0},
	{5'b0, phase_shoot,10'b0},
	{3'b0, o_hp_p1,10'b0},
	{5'b0, {o_handcuff_active & playerA},10'b0}, // o_handcuff_active & playerA 
	{3'b0, item_number0_p1,10'b0},
	{3'b0, item_number1_p1,10'b0},
	{3'b0, item_number2_p1,10'b0},
	{3'b0, item_number3_p1,10'b0},
	{3'b0, item_number4_p1,10'b0},
	{3'b0, item_number5_p1,10'b0},
	{3'b0, item_number6_p1,10'b0},
	{3'b0, o_hp_p0,10'b0},
	{5'b0, {o_handcuff_active & playerB},10'b0}, // o_handcuff_active & playerA 
	{3'b0, item_number0_p0,10'b0},
	{3'b0, item_number1_p0,10'b0},
	{3'b0, item_number2_p0,10'b0},
	{3'b0, item_number3_p0,10'b0},
	{3'b0, item_number4_p0,10'b0},
	{3'b0, item_number5_p0,10'b0},
	{3'b0, item_number6_p0,10'b0},
	{4'b0, bullet_bitmap_p1[0],10'b0},
	{4'b0, bullet_bitmap_p1[1],10'b0},
	{4'b0, bullet_bitmap_p1[2],10'b0},
	{4'b0, bullet_bitmap_p1[3],10'b0},
	{4'b0, bullet_bitmap_p1[4],10'b0},
	{4'b0, bullet_bitmap_p1[5],10'b0},
	{4'b0, bullet_bitmap_p1[6],10'b0},
	{4'b0, bullet_bitmap_p1[7],10'b0}
};

RL_model p0(
	.clk(i_clk),
	.rst_n(i_rst_n),
	.start(start_ai_p0),
	.in_vec(p0_in_vec),
	.action(action_p0)
);

RL_model p1(
	.clk(i_clk),
	.rst_n(i_rst_n),
	.start(start_ai_p1),
	.in_vec(p1_in_vec),
	.action(action_p1)
);


assign  LEDR[17:0] = 1'b1 << state;

// Button Assignments

// Button_proc Button_proc_inst (
// 	.i_clk(i_clk),
// 	.i_rst_n(i_rst_n),
// 	.i_exist(SW[15]),
// 	.i_sparkle(sparkle),
// 	.i_button(GPIO[1]),
// 	.o_button(GPIO[2]),
// 	.o_select()
// );

Button_proc p0_0 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p0[0][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[8]),
	.o_button(GPIO[9]),
	.o_select(item_select_player0[0])
);
Button_proc p0_1 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p0[1][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[6]),
	.o_button(GPIO[7]),
	.o_select(item_select_player0[1])
);
Button_proc p0_2 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p0[2][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[10]),
	.o_button(GPIO[11]),
	.o_select(item_select_player0[2])
);
Button_proc p0_3 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p0[3][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[4]),
	.o_button(GPIO[5]),
	.o_select(item_select_player0[3])
);
Button_proc p0_4 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p0[4][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[2]),
	.o_button(GPIO[3]),
	.o_select(item_select_player0[4])
);
Button_proc p0_5 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p0[5][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[0]),
	.o_button(GPIO[1]),
	.o_select(item_select_player0[5])
);
// Due to fucking DE2-115
Button_proc p1_0 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p1[0][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[34]),
	.o_button(GPIO[35]),
	.o_select(item_select_player1[0])
);
Button_proc p1_1 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p1[1][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[32]),
	.o_button(GPIO[33]),
	.o_select(item_select_player1[1])
);
Button_proc p1_2 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p1[2][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[30]),
	.o_button(GPIO[31]),
	.o_select(item_select_player1[2])
);
Button_proc p1_3 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p1[3][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[24]),
	.o_button(GPIO[25]),
	.o_select(item_select_player1[3])
);
// Modified since 28 29 broken
Button_proc p1_4 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p1[4][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[22]),
	.o_button(GPIO[23]),
	.o_select(item_select_player1[4])
);
Button_proc p1_5 (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_exist(item_column_p1[5][3]),
	.i_sparkle(sparkle),
	.i_button(GPIO[26]),
	.o_button(GPIO[27]),
	.o_select(item_select_player1[5])
);

endmodule
