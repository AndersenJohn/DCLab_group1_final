module Game_logic (
	input        i_clk,
	input        i_rst_n,
	input        i_start,
	input        i_uart_done,
	input   	 i_item_shoot, // 1: shoot, 0: use item
	input [5:0]  i_item_select, // item_select[5:0] 對應桌上 6 個道具位置
	input 		 i_shoot_trigger, // 1: shoot action triggered
	input 		 i_shoot_select, // 0: shoot self, 1: shoot player
	// output
	output [2:0] o_hp_p0, 
	output [2:0] o_hp_p1, 
	output [3:0] o_bullet_bitmap_ptr, 
	output [3:0] o_total_bullet, 
	output [3:0] o_total_bullet_remaining, 
	output [2:0] o_bullet_filled, 
	output [2:0] o_bullet_empty, 
	output       o_bullet_report_valid, 
	output       o_bullet_report, 
	output [2:0] o_report_idx, 
	output [1:0] o_winner, 
	// item positions 
	output [3:0] o_item_column_p0_0,
	output [3:0] o_item_column_p0_1,
	output [3:0] o_item_column_p0_2,
	output [3:0] o_item_column_p0_3,
	output [3:0] o_item_column_p0_4,
	output [3:0] o_item_column_p0_5,
	output [3:0] o_item_column_p1_0,
	output [3:0] o_item_column_p1_1,
	output [3:0] o_item_column_p1_2,
	output [3:0] o_item_column_p1_3,
	output [3:0] o_item_column_p1_4,
	output [3:0] o_item_column_p1_5,
	// state
	output [3:0] o_state,
	// player
	output       o_playerA,
	output       o_playerB,
	// bullet bitmap
	output [7:0] o_bullet_bitmap,
	// active
	output       o_saw_active,
	output       o_reverse_active,
	output	     o_handcuff_active,
	// shock
	output       o_shock,
	// bullet num initial
	output [3:0] o_bullet_num_initial0,
	output [3:0] o_bullet_num_initial1,
	output [3:0] o_bullet_num_initial2,
	output [3:0] o_bullet_num_initial3    
);

// ===== States =====
logic [3:0] state_r, state_w;
parameter S_IDLE = 4'd0;
parameter S_LOAD = 4'd1;
parameter S_ITEM_P0 = 4'd2;
parameter S_ITEM_P1 = 4'd3;
parameter S_ITEM_PROC = 4'd4;
parameter S_SHOOT_P0 = 4'd5;
parameter S_SHOOT_P1 = 4'd6;
parameter S_SHOOT_PROC = 4'd7;
parameter S_DONE = 4'd8;

parameter S_ITEM_INTO_LOAD = 4'd9;
parameter S_SHOOT_INTO_LOAD = 4'd10;
parameter S_INTO_ITEM_P0_WAIT = 4'd11;
parameter S_INTO_ITEM_P1_WAIT = 4'd12;
parameter S_SHOOT_INTO_P0_WAIT = 4'd13;
parameter S_SHOOT_INTO_P1_WAIT = 4'd14;
parameter S_INTO_DONE = 4'd15;

logic [3:0] time_value;

// ===== actions(item) ======
// Magnifier, Cigarette, Handcuff, Saw, Beer, Phone, Reverse, Gun
// 8, 9, 10, 11, 12, 13, 14, 15
parameter use_magnifier = {1'b1, 3'd0};
parameter use_cigarette = {1'b1, 3'd1};
parameter use_handcuff = {1'b1, 3'd2};
parameter use_saw = {1'b1, 3'd3};
parameter use_beer = {1'b1, 3'd4};
parameter use_phone = {1'b1, 3'd5};
parameter use_reverse = {1'b1, 3'd6};
parameter use_gun = {1'b1, 3'd7};

// ===== actions(shoot) ======
parameter shoot_self = {1'b1, 3'd0};
parameter shoot_player = {1'b1, 3'd1};


// ===== Item wire/reg =====
logic report_bullet_valid_w, report_bullet_valid_r;
logic report_bullet_w, report_bullet_r;
logic [2:0] report_idx_w, report_idx_r;

logic saw_active_w, saw_active_r;
logic reverse_active_w, reverse_active_r;
logic handcuff_active_w, handcuff_active_r;
assign o_saw_active = saw_active_r;
assign o_reverse_active = reverse_active_r;
assign o_handcuff_active = handcuff_active_r;

logic report_bullet_valid_item;
logic report_bullet_item;
logic [2:0] report_idx_item;
logic [3:0] hp_p0_item, hp_p1_item;
logic [3:0] bitmap_ptr_item;
logic saw_active_item;
logic reverse_active_item;
logic handcuff_active_item;


// ===== Action / Player =====
logic [3:0] action; // action[3] 表示動作開始，action[2:0] 表示動作種類
logic [3:0] action_proc_w, action_proc_r;

logic playerA_w, playerB_w, playerA_r, playerB_r; // playerA 對 playerB 開槍/使用道具
// always @(*) begin
// 	playerA_w = playerA_r;
// 	playerB_w = playerB_r;
// 	if (state_r == S_SHOOT_P0 || state_r == S_ITEM_P0) begin
// 		playerA_w = 0;
// 		playerB_w = 1;
// 	end
// 	else if (state_r == S_SHOOT_P1 || state_r == S_ITEM_P1) begin
// 		playerA_w = 1;
// 		playerB_w = 0;
// 	end
// 	else if (state_r == S_IDLE) begin
// 		playerA_w = 1;
// 		playerB_w = 0;
// 	end
// end



// ===== static status =====
logic [1:0] winner_w, winner_r; // 00: none, 01: player0 win, 10: player1 win
logic signed [3:0] hp_p0_w, hp_p0_r;
logic signed [3:0] hp_p1_w, hp_p1_r;

logic [7:0] bullet_bitmap_w, bullet_bitmap_r, bullet_bitmap_update;
// logic [7:0] bullet_bitmap0, bullet_bitmap1, bullet_bitmap2, bullet_bitmap3;
logic [3:0] bullet_bitmap_ptr_w, bullet_bitmap_ptr_r;
logic [3:0] bullet_num;
logic [1:0] bullet_num_ctr_w, bullet_num_ctr_r;
logic [3:0] bullet_num_initial [0:3];

assign o_bullet_num_initial0 = bullet_num_initial[0];
assign o_bullet_num_initial1 = bullet_num_initial[1];
assign o_bullet_num_initial2 = bullet_num_initial[2];
assign o_bullet_num_initial3 = bullet_num_initial[3];

logic [2:0] item_gen_p0 [0:5];
logic [2:0] item_gen_p1 [0:5];

logic [3:0] item_column_p0_w [0:5]; //   放置位置：
logic [3:0] item_column_p0_r [0:5]; //		    [2]	   [3]
logic [3:0] item_column_p1_w [0:5]; //	 [0]    [1]	   [4]	  [5]
logic [3:0] item_column_p1_r [0:5]; //


// ===== Output Buffers =====
assign o_hp_p0 = hp_p0_r[2:0];
assign o_hp_p1 = hp_p1_r[2:0];
assign o_bullet_bitmap_ptr = bullet_bitmap_ptr_r;
assign o_bullet_report_valid = report_bullet_valid_r;
assign o_bullet_report = report_bullet_r;
assign o_report_idx = report_idx_r;
assign o_winner = winner_r;
assign o_total_bullet = bullet_num;
assign o_total_bullet_remaining = bullet_num - bullet_bitmap_ptr_r;
assign o_bullet_filled = (bullet_bitmap_r[0] && bullet_bitmap_ptr_r <= 4'd0 && 4'd0 < bullet_num) + 
                         (bullet_bitmap_r[1] && bullet_bitmap_ptr_r <= 4'd1 && 4'd1 < bullet_num) + 
                         (bullet_bitmap_r[2] && bullet_bitmap_ptr_r <= 4'd2 && 4'd2 < bullet_num) + 
                         (bullet_bitmap_r[3] && bullet_bitmap_ptr_r <= 4'd3 && 4'd3 < bullet_num) + 
                         (bullet_bitmap_r[4] && bullet_bitmap_ptr_r <= 4'd4 && 4'd4 < bullet_num) + 
                         (bullet_bitmap_r[5] && bullet_bitmap_ptr_r <= 4'd5 && 4'd5 < bullet_num) + 
                         (bullet_bitmap_r[6] && bullet_bitmap_ptr_r <= 4'd6 && 4'd6 < bullet_num) + 
                         (bullet_bitmap_r[7] && bullet_bitmap_ptr_r <= 4'd7 && 4'd7 < bullet_num);
assign o_bullet_empty = o_total_bullet_remaining - o_bullet_filled;

assign o_item_column_p0_0 = item_column_p0_r[0];
assign o_item_column_p0_1 = item_column_p0_r[1];
assign o_item_column_p0_2 = item_column_p0_r[2];
assign o_item_column_p0_3 = item_column_p0_r[3];
assign o_item_column_p0_4 = item_column_p0_r[4];
assign o_item_column_p0_5 = item_column_p0_r[5];
assign o_item_column_p1_0 = item_column_p1_r[0];
assign o_item_column_p1_1 = item_column_p1_r[1];
assign o_item_column_p1_2 = item_column_p1_r[2];
assign o_item_column_p1_3 = item_column_p1_r[3];
assign o_item_column_p1_4 = item_column_p1_r[4];
assign o_item_column_p1_5 = item_column_p1_r[5];
assign o_state = state_r;
assign o_playerA = playerA_r;
assign o_playerB = playerB_r;
assign o_bullet_bitmap = bullet_bitmap_r;

    

// modules 
Time_Gen time_gen (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.o_time(time_value)
);

Bullet_num_Gen bullet_num_gen (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_start(i_start & (state_r == S_IDLE)),
	.i_time(time_value),
	.o1(bullet_num_initial[0]),
	.o2(bullet_num_initial[1]),
	.o3(bullet_num_initial[2]),
	.o4(bullet_num_initial[3])
);

Bullet_Item_Gen bullet_item_gen (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_time(time_value),
	.i_hp_p0(hp_p0_r[2:0]),
	.i_hp_p1(hp_p1_r[2:0]),
	.i_bullet_num(bullet_num),
	.o_bullet_bitmap(bullet_bitmap_update),
	.o_item1_p0(item_gen_p0[0]),
	.o_item2_p0(item_gen_p0[1]),
	.o_item3_p0(item_gen_p0[2]),
	.o_item4_p0(item_gen_p0[3]),
	.o_item5_p0(item_gen_p0[4]),
	.o_item6_p0(item_gen_p0[5]),
	.o_item1_p1(item_gen_p1[0]),
	.o_item2_p1(item_gen_p1[1]),
	.o_item3_p1(item_gen_p1[2]),
	.o_item4_p1(item_gen_p1[3]),
	.o_item5_p1(item_gen_p1[4]),
	.o_item6_p1(item_gen_p1[5])
);
Use_Item use_item (
	.i_clk(i_clk),
	.i_rst_n(i_rst_n),
	.i_use_item(action[3]),
	.i_item(action[2:0]),
	.i_bullet_bitmap(bullet_bitmap_r),
	.i_bullet_bitmap_ptr(bullet_bitmap_ptr_r),
	.i_hp_p1(hp_p0_r),
	.i_hp_p2(hp_p1_r),
	.i_saw_active(saw_active_r),
	.i_reverse_active(reverse_active_r),
	.i_handcuff_active(handcuff_active_r),
	.i_playerA(playerA_r),
	.i_playerB(playerB_r),
	.i_total_bullet_remaining(bullet_num - bullet_bitmap_ptr_r),
	.i_time(time_value),
	.i_total_bullet(bullet_num),
	.o_bullet_report_valid(report_bullet_valid_item),
	.o_bullet_report(report_bullet_item),
	.o_report_idx(report_idx_item),
	.o_hp_p1_report(hp_p0_item),
	.o_hp_p2_report(hp_p1_item),
	.o_saw_active(saw_active_item),
	.o_bitmap_ptr(bitmap_ptr_item),
	.o_reverse_active(reverse_active_item),
	.o_handcuff_active(handcuff_active_item)
);

// ===== Output Assignments =====


// ===== Shock Assignments =====
logic shock_w, shock_r;
assign o_shock = shock_r;
always @(posedge i_clk or negedge i_rst_n) begin
	if (!i_rst_n) begin
		shock_r <= 1'b0;
	end
	else begin
		shock_r <= shock_w;
	end
end

// ===== FSM =====
assign bullet_num = bullet_num_initial[bullet_num_ctr_r];
always @(*) begin
	state_w = state_r;
	winner_w = 2'b00;
	bullet_bitmap_ptr_w = bullet_bitmap_ptr_r;
	bullet_bitmap_w = bullet_bitmap_r;
	bullet_num_ctr_w = bullet_num_ctr_r;

	report_bullet_valid_w = report_bullet_valid_r;
	report_bullet_w = report_bullet_r;
	report_idx_w = report_idx_r;

	saw_active_w = saw_active_r;
	reverse_active_w = reverse_active_r;
	handcuff_active_w = handcuff_active_r;

	playerA_w = playerA_r;
	playerB_w = playerB_r;
	
	
	case (state_r)
		S_IDLE: begin
			playerA_w = 1; // player 1 先手
			playerB_w = 0;
			if (i_start) begin
				state_w = S_LOAD;
				// bullet_num_w = bullet_num_initial[0];
			end
		end
		S_LOAD: begin
			state_w = (playerA_r & ~playerB_r) ? S_INTO_ITEM_P1_WAIT : S_INTO_ITEM_P0_WAIT;
			bullet_bitmap_ptr_w = 4'd0;
			bullet_bitmap_w = bullet_bitmap_update; // load new bullet bitmap
			// 新增這個
			// bullet_num_w = bullet_num_initial[bullet_num_ctr_r];
			saw_active_w = 1'b0;
			reverse_active_w = 1'b0;
			handcuff_active_w = 1'b0;
		end
		S_ITEM_P0: begin
			playerA_w = 0;
			playerB_w = 1;
			if (action == use_gun) begin
				state_w = S_SHOOT_P0;
			end
			else if (action[3]) begin
				state_w = S_ITEM_PROC;
			end
		end
		S_SHOOT_P0: begin
			playerA_w = 0;
			playerB_w = 1;
			if (action[3]) begin
				state_w = S_SHOOT_PROC;
			end
		end
		S_ITEM_P1: begin
			playerA_w = 1;
			playerB_w = 0;
			if (action == use_gun) begin
				state_w = S_SHOOT_P1;
			end
			else if (action[3]) begin
				state_w = S_ITEM_PROC;
			end
		end
		S_SHOOT_P1: begin
			playerA_w = 1;
			playerB_w = 0;
			if (action[3]) begin
				state_w = S_SHOOT_PROC;
			end
		end
		S_ITEM_PROC: begin
			if (playerA_r & ~playerB_r) begin
				state_w = S_INTO_ITEM_P1_WAIT;
			end
			else if (~playerA_r & playerB_r) begin
				state_w = S_INTO_ITEM_P0_WAIT;
			end

			if (action_proc_r[3]) begin
				// update item results
				// hp_p0_w = hp_p0_item;
				// hp_p1_w = hp_p1_item;
				// if (hp_p0_w == 4'd0 || hp_p0_w == -4'd1 || hp_p1_w == 4'd0 || hp_p1_w == -4'd1) begin
				// 	winner_w = {playerA_r, playerB_r};
				// 	state_w = S_DONE;
				// end
				bullet_bitmap_ptr_w = bitmap_ptr_item;
				report_bullet_valid_w = report_bullet_valid_item;
				report_bullet_w = report_bullet_item;
				report_idx_w = report_idx_item;
				saw_active_w = saw_active_item;
				reverse_active_w = reverse_active_item;
				handcuff_active_w = handcuff_active_item;
				if (bitmap_ptr_item == bullet_num) begin
					state_w = S_ITEM_INTO_LOAD;
					bullet_num_ctr_w = (bullet_num_ctr_r == 2'd3) ? 2'd1 : bullet_num_ctr_r + 2'd1;
					// Comment out 這個
					// bullet_num_w = bullet_num_initial[bullet_num_ctr_r];
				end
			end
		end
		S_SHOOT_PROC: begin
			report_bullet_valid_w = 1'b0;
			report_bullet_w = 1'b0;
			report_idx_w = 3'd0;
			saw_active_w = 1'b0;
			reverse_active_w = 1'b0;


			if (hp_p0_w == 4'd0 || hp_p0_w == -4'd1 || hp_p1_w == 4'd0 || hp_p1_w == -4'd1) begin
				winner_w = {playerA_r, playerB_r};
				state_w = S_INTO_DONE;
				bullet_bitmap_ptr_w = bullet_bitmap_ptr_r + 4'd1;
			end
			else begin
				if (bullet_bitmap_ptr_r + 4'd1 == bullet_num) begin
					state_w = S_SHOOT_INTO_LOAD;
					bullet_num_ctr_w = (bullet_num_ctr_r == 2'd3) ? 2'd1 : bullet_num_ctr_r + 2'd1;
					// Comment out 這個
					// bullet_num_w = bullet_num_initial[bullet_num_ctr_r];
					if (action_proc_r == shoot_player || (action_proc_r == shoot_self && (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r))) begin
						playerA_w = ~playerA_r;
						playerB_w = ~playerB_r;
					end
					// 改新增這個
					bullet_bitmap_ptr_w = bullet_num;
				end
				else if ((((playerA_r & ~playerB_r) && action_proc_r == shoot_player) || ((playerA_r & ~playerB_r) && action_proc_r == shoot_self && (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r))) && handcuff_active_r) begin
					handcuff_active_w = 1'b0;
					state_w = S_SHOOT_INTO_P1_WAIT;
					bullet_bitmap_ptr_w = bullet_bitmap_ptr_r + 4'd1;
				end
				else if ((((~playerA_r & playerB_r) && action_proc_r == shoot_player) || ((~playerA_r & playerB_r) && action_proc_r == shoot_self && (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r))) && handcuff_active_r) begin
					handcuff_active_w = 1'b0;
					state_w = S_SHOOT_INTO_P0_WAIT;
					bullet_bitmap_ptr_w = bullet_bitmap_ptr_r + 4'd1;
				end
				else if (((playerA_r & ~playerB_r) && action_proc_r == shoot_player) || ((playerA_r & ~playerB_r) && action_proc_r == shoot_self && (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r)) || ((~playerA_r & playerB_r) && action_proc_r == shoot_self && ~((bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r)))) begin
					state_w = S_SHOOT_INTO_P0_WAIT;
					bullet_bitmap_ptr_w = bullet_bitmap_ptr_r + 4'd1;
				end
				else if (((~playerA_r & playerB_r) && action_proc_r == shoot_player) || ((~playerA_r & playerB_r) && action_proc_r == shoot_self && (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r)) || ((playerA_r & ~playerB_r) && action_proc_r == shoot_self && ~((bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r)))) begin
					state_w = S_SHOOT_INTO_P1_WAIT;
					bullet_bitmap_ptr_w = bullet_bitmap_ptr_r + 4'd1;
				end
			end
		end
		S_DONE: begin
			winner_w = winner_r;
		end

		S_ITEM_INTO_LOAD: begin
			if (i_uart_done) begin
				state_w = S_LOAD;
			end
			else begin
				state_w = S_ITEM_INTO_LOAD;
			end
		end

		S_SHOOT_INTO_LOAD: begin
			if (i_uart_done) begin
				state_w = S_LOAD;
			end
			else begin
				state_w = S_SHOOT_INTO_LOAD;
			end
		end

		S_INTO_ITEM_P0_WAIT: begin
			if (i_uart_done) begin
				state_w = S_ITEM_P0;
			end
			else begin
				state_w = S_INTO_ITEM_P0_WAIT;
			end
		end

		S_INTO_ITEM_P1_WAIT: begin
			if (i_uart_done) begin
				state_w = S_ITEM_P1;
			end
			else begin
				state_w = S_INTO_ITEM_P1_WAIT;
			end
		end

		S_SHOOT_INTO_P0_WAIT: begin
			if (i_uart_done) begin
				state_w = S_ITEM_P0;
			end
			else begin
				state_w = S_SHOOT_INTO_P0_WAIT;
			end
		end

		S_SHOOT_INTO_P1_WAIT: begin
			if (i_uart_done) begin
				state_w = S_ITEM_P1;
			end
			else begin
				state_w = S_SHOOT_INTO_P1_WAIT;
			end
		end

		S_INTO_DONE : begin
			if (i_uart_done) begin
				state_w = S_DONE;
			end
			else begin
				state_w = S_INTO_DONE;
			end
		end
		default: begin
			
		end
	endcase
end

// ===== load items ===== 
integer i;
integer k;
integer limit;
always @(*) begin
	for (i = 0; i < 6; i = i + 1) begin
		item_column_p0_w[i] = item_column_p0_r[i];
		item_column_p1_w[i] = item_column_p1_r[i];
	end
	case (state_r)
		S_LOAD: begin
			// Determine limit based on bullet count
			if (bullet_num >= 4'd8) limit = 3;
			else if (bullet_num >= 4'd6) limit = 2;
			else limit = 1;

			// Player 0 Filling
			k = 0;
			for (i = 0; i < 6; i = i + 1) begin
				if (item_column_p0_r[i][3]) begin
					item_column_p0_w[i] = item_column_p0_r[i]; // Keep existing
				end
				else if (k < limit) begin
					item_column_p0_w[i] = {1'b1, item_gen_p0[i]}; // Add new
					k = k + 1;
				end
				else begin
					item_column_p0_w[i] = 4'd0; // Keep empty
				end
			end

			// Player 1 Filling
			k = 0;
			for (i = 0; i < 6; i = i + 1) begin
				if (item_column_p1_r[i][3]) begin
					item_column_p1_w[i] = item_column_p1_r[i]; // Keep existing
				end
				else if (k < limit) begin
					item_column_p1_w[i] = {1'b1, item_gen_p1[i]}; // Add new
					k = k + 1;
				end
				else begin
					item_column_p1_w[i] = 4'd0; // Keep empty
				end
			end
		end
		S_ITEM_P0: begin
			if (action[3] && action != use_gun) begin
				// remove used item
				case (i_item_select) // synopsys full_case
					6'b000001: item_column_p0_w[0] = 4'd0;
					6'b000010: item_column_p0_w[1] = 4'd0;
					6'b000100: item_column_p0_w[2] = 4'd0;
					6'b001000: item_column_p0_w[3] = 4'd0;
					6'b010000: item_column_p0_w[4] = 4'd0;
					6'b100000: item_column_p0_w[5] = 4'd0;
					6'b000000: ;
				endcase
			end
		end
		S_ITEM_P1: begin
			if (action[3] && action != use_gun) begin
				// remove used item
				case (i_item_select) // synopsys full_case
					6'b000001: item_column_p1_w[0] = 4'd0;
					6'b000010: item_column_p1_w[1] = 4'd0;
					6'b000100: item_column_p1_w[2] = 4'd0;
					6'b001000: item_column_p1_w[3] = 4'd0;
					6'b010000: item_column_p1_w[4] = 4'd0;
					6'b100000: item_column_p1_w[5] = 4'd0;
					6'b000000: ;
				endcase
			end
		end
	endcase
end

assign action_proc_w = action;
// ===== Action verification ===== (把 按鈕、桌上item位置、state 對應成 action )
always @(*) begin
	// Default Values
	action = 3'd0;
	// FSM
	case (state_r)
		S_ITEM_P0: begin
			if (!i_item_shoot && i_item_select) begin // use item
				case (i_item_select) // synopsys full_case
					6'b000001: action = (item_column_p0_r[0][3]) ? item_column_p0_r[0][3:0] : 4'd0;
					6'b000010: action = (item_column_p0_r[1][3]) ? item_column_p0_r[1][3:0] : 4'd0;
					6'b000100: action = (item_column_p0_r[2][3]) ? item_column_p0_r[2][3:0] : 4'd0;
					6'b001000: action = (item_column_p0_r[3][3]) ? item_column_p0_r[3][3:0] : 4'd0;
					6'b010000: action = (item_column_p0_r[4][3]) ? item_column_p0_r[4][3:0] : 4'd0;
					6'b100000: action = (item_column_p0_r[5][3]) ? item_column_p0_r[5][3:0] : 4'd0;
				endcase
			end
			else if (i_item_shoot) begin // shoot
				action = use_gun;
			end
		end
		S_ITEM_P1: begin
			if (!i_item_shoot && i_item_select) begin // use item
				case (i_item_select) // synopsys full_case
					6'b000001: action = (item_column_p1_r[0][3]) ? item_column_p1_r[0][3:0] : 4'd0;
					6'b000010: action = (item_column_p1_r[1][3]) ? item_column_p1_r[1][3:0] : 4'd0;
					6'b000100: action = (item_column_p1_r[2][3]) ? item_column_p1_r[2][3:0] : 4'd0;
					6'b001000: action = (item_column_p1_r[3][3]) ? item_column_p1_r[3][3:0] : 4'd0;
					6'b010000: action = (item_column_p1_r[4][3]) ? item_column_p1_r[4][3:0] : 4'd0;
					6'b100000: action = (item_column_p1_r[5][3]) ? item_column_p1_r[5][3:0] : 4'd0;
				endcase
			end
			else if (i_item_shoot) begin // shoot
				action = use_gun;
			end
		end
		// S_ITEM_PROC: begin
		// 	action = 4'd0;
		// end
		S_SHOOT_P0: begin
			if (i_shoot_trigger) begin
				action = (i_shoot_select) ? shoot_player : shoot_self;
			end
		end
		S_SHOOT_P1: begin
			if (i_shoot_trigger) begin
				action = (i_shoot_select) ? shoot_player : shoot_self;
			end
		end
		S_ITEM_PROC, S_SHOOT_PROC: begin
			action = action_proc_r;
		end
	endcase
	
end

// ===== Shoot Results ===== ( 處理 hp )
always @(*) begin
	// Default Values
	hp_p0_w = hp_p0_r;
	hp_p1_w = hp_p1_r;

	shock_w = 1'b0;

	// FSM
	case (state_r)
		S_ITEM_PROC: begin
			hp_p0_w = hp_p0_item;
			hp_p1_w = hp_p1_item;
		end
		S_SHOOT_PROC: begin
			if (~playerA_r & playerB_r) begin
				if (action_proc_r == shoot_player) begin
					hp_p1_w = (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r) ? (hp_p1_r == 3'd1) ? hp_p1_r - 3'd1 : hp_p1_r - (3'd1 + saw_active_r) : hp_p1_r;
				end
				else if (action_proc_r == shoot_self) begin
					hp_p0_w = (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r) ? (hp_p0_r == 3'd1) ? hp_p0_r - 3'd1 : hp_p0_r - (3'd1 + saw_active_r) : hp_p0_r;
				end
			end
			else if (playerA_r & ~playerB_r) begin
				if (action_proc_r == shoot_player) begin
					hp_p0_w = (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r) ? (hp_p0_r == 3'd1) ? hp_p0_r - 3'd1 : hp_p0_r - (3'd1 + saw_active_r) : hp_p0_r;
				end
				else if (action_proc_r == shoot_self) begin
					hp_p1_w = (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r) ? (hp_p1_r == 3'd1) ? hp_p1_r - 3'd1 : hp_p1_r - (3'd1 + saw_active_r) : hp_p1_r;
				end
			end
			// shock process
			if (bullet_bitmap_r[bullet_bitmap_ptr_r] ^ reverse_active_r) begin
				shock_w = 1'b1;
			end
		end
	endcase
end

// ===== Sequential Circuits =====
integer j;
always @(posedge i_clk or negedge i_rst_n) begin
	// reset
	if (!i_rst_n) begin
		state_r <= S_IDLE;
		report_bullet_valid_r <= 1'b0;
		report_bullet_r <= 1'b0;
		report_idx_r <= 3'd0;
		saw_active_r <= 1'b0;
		reverse_active_r <= 1'b0;
		handcuff_active_r <= 1'b0;
		action_proc_r <= 4'd0;
		playerA_r <= 1'b0;
		playerB_r <= 1'b0;
		winner_r <= 2'b00;
		hp_p0_r <= 4'd4;
		hp_p1_r <= 4'd4;
		bullet_bitmap_r <= 8'd0;
		bullet_bitmap_ptr_r <= 4'd0;
		// bullet_num_r <= 4'd0;
		bullet_num_ctr_r <= 2'd0;
		for (j = 0; j < 6; j = j + 1) begin
			item_column_p0_r[j] <= 4'd0;
			item_column_p1_r[j] <= 4'd0;
		end
	end
	else begin
		state_r <= state_w;
		report_bullet_valid_r <= report_bullet_valid_w;
		report_bullet_r <= report_bullet_w;
		report_idx_r <= report_idx_w;
		saw_active_r <= saw_active_w;
		reverse_active_r <= reverse_active_w;
		handcuff_active_r <= handcuff_active_w;
		action_proc_r <= action_proc_w;
		playerA_r <= playerA_w;
		playerB_r <= playerB_w;
		winner_r <= winner_w;
		hp_p0_r <= hp_p0_w;
		hp_p1_r <= hp_p1_w;
		bullet_bitmap_r <= bullet_bitmap_w;
		bullet_bitmap_ptr_r <= bullet_bitmap_ptr_w;
		// bullet_num_r <= bullet_num_w;
		bullet_num_ctr_r <= bullet_num_ctr_w;
		for (j = 0; j < 6; j = j + 1) begin
			item_column_p0_r[j] <= item_column_p0_w[j];
			item_column_p1_r[j] <= item_column_p1_w[j];
		end
	end
end

endmodule