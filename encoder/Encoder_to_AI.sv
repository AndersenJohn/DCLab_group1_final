module Encoder_to_AI #(parameter AI_Player = 0) (
	input       	   clk,
	input       	   rst_n,
	input [2:0] 	   hp_p0,
	input [2:0] 	   hp_p1,
	input [3:0] 	   bullet_bitmap_ptr,
	input [3:0] 	   total_bullet,
	input [3:0] 	   total_bullet_remaining,
	input [2:0] 	   bullet_filled,
	input [2:0] 	   bullet_empty,
	input       	   bullet_report_valid,
	input       	   bullet_report,
	input [2:0] 	   report_idx,
	input [3:0] 	   item0_p0,
	input [3:0] 	   item1_p0,
	input [3:0] 	   item2_p0,
	input [3:0] 	   item3_p0,
	input [3:0] 	   item4_p0,
	input [3:0] 	   item5_p0,
	input [3:0] 	   item0_p1,
	input [3:0] 	   item1_p1,
	input [3:0] 	   item2_p1,
	input [3:0] 	   item3_p1,
	input [3:0] 	   item4_p1,
	input [3:0] 	   item5_p1,
	input [3:0] 	   state,
	input 			   playerA,
	input 			   playerB,
	input [7:0] 	   bullet_bitmap,
	// outputs
	output [2:0] 	   o_item_number0_p0,
	output [2:0] 	   o_item_number1_p0,
	output [2:0] 	   o_item_number2_p0,
	output [2:0] 	   o_item_number3_p0,
	output [2:0] 	   o_item_number4_p0,
	output [2:0] 	   o_item_number5_p0,
	output [2:0] 	   o_item_number6_p0,
	output [2:0] 	   o_item_number0_p1,
	output [2:0] 	   o_item_number1_p1,
	output [2:0] 	   o_item_number2_p1,
	output [2:0] 	   o_item_number3_p1,
	output [2:0] 	   o_item_number4_p1,
	output [2:0] 	   o_item_number5_p1,
	output [2:0] 	   o_item_number6_p1,
	output 			   o_phase_item,
	output 			   o_phase_shoot,
	output [1:0] 	   bullet_bitmap_p0_0,
	output [1:0] 	   bullet_bitmap_p0_1,
	output [1:0] 	   bullet_bitmap_p0_2,
	output [1:0] 	   bullet_bitmap_p0_3,
	output [1:0] 	   bullet_bitmap_p0_4,
	output [1:0] 	   bullet_bitmap_p0_5,
	output [1:0] 	   bullet_bitmap_p0_6,
	output [1:0] 	   bullet_bitmap_p0_7,
	output [1:0] 	   bullet_bitmap_p1_0,
	output [1:0] 	   bullet_bitmap_p1_1,
	output [1:0] 	   bullet_bitmap_p1_2,
	output [1:0] 	   bullet_bitmap_p1_3,
	output [1:0] 	   bullet_bitmap_p1_4,
	output [1:0] 	   bullet_bitmap_p1_5,
	output [1:0] 	   bullet_bitmap_p1_6,
	output [1:0] 	   bullet_bitmap_p1_7,

	output o_start

);



logic [3:0] item_column_p0 [0:5];
logic [3:0] item_column_p1 [0:5];
assign item_column_p0[0] = item0_p0;
assign item_column_p0[1] = item1_p0;
assign item_column_p0[2] = item2_p0;
assign item_column_p0[3] = item3_p0;
assign item_column_p0[4] = item4_p0;
assign item_column_p0[5] = item5_p0;
assign item_column_p1[0] = item0_p1;
assign item_column_p1[1] = item1_p1;
assign item_column_p1[2] = item2_p1;
assign item_column_p1[3] = item3_p1;
assign item_column_p1[4] = item4_p1;
assign item_column_p1[5] = item5_p1;

logic [2:0] item_number0_p0, item_number1_p0, item_number2_p0, item_number3_p0, item_number4_p0, item_number5_p0, item_number6_p0;
logic [2:0] item_number0_p1, item_number1_p1, item_number2_p1, item_number3_p1, item_number4_p1, item_number5_p1, item_number6_p1;
assign o_item_number0_p0 = item_number0_p0;
assign o_item_number1_p0 = item_number1_p0;
assign o_item_number2_p0 = item_number2_p0;
assign o_item_number3_p0 = item_number3_p0;
assign o_item_number4_p0 = item_number4_p0;
assign o_item_number5_p0 = item_number5_p0;
assign o_item_number6_p0 = item_number6_p0;
assign o_item_number0_p1 = item_number0_p1;
assign o_item_number1_p1 = item_number1_p1;
assign o_item_number2_p1 = item_number2_p1;
assign o_item_number3_p1 = item_number3_p1;
assign o_item_number4_p1 = item_number4_p1;
assign o_item_number5_p1 = item_number5_p1;
assign o_item_number6_p1 = item_number6_p1;

logic phase_item, phase_shoot;
assign phase_item = (state == 4'd2 || state == 4'd3) ? 1'b1 : 1'b0;
assign phase_shoot = (state == 4'd5 || state == 4'd6) ? 1'b1 : 1'b0;
assign o_phase_item = phase_item;
assign o_phase_shoot = phase_shoot;

logic [1:0] bullet_bitmap_p0_r [0:7];
logic [1:0] bullet_bitmap_p0_w [0:7];
logic [1:0] bullet_bitmap_p1_r [0:7];
logic [1:0] bullet_bitmap_p1_w [0:7];
assign bullet_bitmap_p0_0 = bullet_bitmap_p0_r[0];
assign bullet_bitmap_p0_1 = bullet_bitmap_p0_r[1];
assign bullet_bitmap_p0_2 = bullet_bitmap_p0_r[2];
assign bullet_bitmap_p0_3 = bullet_bitmap_p0_r[3];
assign bullet_bitmap_p0_4 = bullet_bitmap_p0_r[4];
assign bullet_bitmap_p0_5 = bullet_bitmap_p0_r[5];
assign bullet_bitmap_p0_6 = bullet_bitmap_p0_r[6];
assign bullet_bitmap_p0_7 = bullet_bitmap_p0_r[7];
assign bullet_bitmap_p1_0 = bullet_bitmap_p1_r[0];
assign bullet_bitmap_p1_1 = bullet_bitmap_p1_r[1];
assign bullet_bitmap_p1_2 = bullet_bitmap_p1_r[2];
assign bullet_bitmap_p1_3 = bullet_bitmap_p1_r[3];
assign bullet_bitmap_p1_4 = bullet_bitmap_p1_r[4];
assign bullet_bitmap_p1_5 = bullet_bitmap_p1_r[5];
assign bullet_bitmap_p1_6 = bullet_bitmap_p1_r[6];
assign bullet_bitmap_p1_7 = bullet_bitmap_p1_r[7];

logic start_w, start_r;
logic [3:0] state_prev;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state_prev <= 4'd0;
    end
    else begin
        state_prev <= state; 
    end
end

logic is_my_turn;
assign is_my_turn = (state == (4'd2 + AI_Player)) || (state == (4'd5 + AI_Player));
assign start_w = is_my_turn && (state != state_prev);

assign o_start = start_r;

// Player 0 Acknowledge Bullet Bitmap Update
integer i;
always@(*) begin
	for (i = 0; i < 8; i = i + 1) begin
		// bullet_bitmap_p0_w = bullet_bitmap_p0_r;
		bullet_bitmap_p0_w[i] = bullet_bitmap_p0_r[i];
		if (i >= total_bullet) begin // Padding
			bullet_bitmap_p0_w[i] = 2'b00;
		end
		else if (state == 4'd1) begin // S_LOAD => Unknown
			bullet_bitmap_p0_w[i] = 2'b01;
		end
		else if (i < bullet_bitmap_ptr) begin // 10 : Live, 11 : Blank
			bullet_bitmap_p0_w[i] = {1'b1, (~bullet_bitmap[i])};
		end
		else if ((~playerA & playerB) && bullet_report_valid && (i == bullet_bitmap_ptr + report_idx) && (bullet_bitmap_p0_r[i] == 2'b01)) begin
			bullet_bitmap_p0_w[i] = {1'b1, (~bullet_report)};
		end
	end
end

always @(posedge clk or negedge rst_n) begin
	if (!rst_n) begin
		for (i = 0; i < 8; i = i + 1) begin
			bullet_bitmap_p0_r[i] <= 2'b0;
		end
	end
	else begin
		for (i = 0; i < 8; i = i + 1) begin
			bullet_bitmap_p0_r[i] <= bullet_bitmap_p0_w[i];
		end
	end
end

// Player 1 Acknowledge Bullet Bitmap Update
always@(*) begin
	for (i = 0; i < 8; i = i + 1) begin
		// bullet_bitmap_p1_w = bullet_bitmap_p1_r;
		bullet_bitmap_p1_w[i] = bullet_bitmap_p1_r[i];
		if (i >= total_bullet) begin
			bullet_bitmap_p1_w[i] = 2'b00;
		end
		else if (state == 4'd1) begin // S_LOAD
			bullet_bitmap_p1_w[i] = 2'b01;
		end
		else if (i < bullet_bitmap_ptr) begin
			bullet_bitmap_p1_w[i] = {1'b1, (~bullet_bitmap[i])};
		end
		else if ((playerA & ~playerB) && bullet_report_valid && (i == bullet_bitmap_ptr + report_idx) && (bullet_bitmap_p1_r[i] == 2'b01)) begin
			bullet_bitmap_p1_w[i] = {1'b1, (~bullet_report)};
		end
	end
end

always @(posedge clk or negedge rst_n) begin
	if (!rst_n) begin
		for (i = 0; i < 8; i = i + 1) begin
			bullet_bitmap_p1_r[i] <= 2'b0;
		end
	end
	else begin
		for (i = 0; i < 8; i = i + 1) begin
			bullet_bitmap_p1_r[i] <= bullet_bitmap_p1_w[i];
		end
	end
end

// P0 Item Number Decoder
ItemNumberDecoder item_number_decoder_p0(
	.i_item0(item_column_p0[0]),
	.i_item1(item_column_p0[1]),
	.i_item2(item_column_p0[2]),
	.i_item3(item_column_p0[3]),
	.i_item4(item_column_p0[4]),
	.i_item5(item_column_p0[5]),
	.o_item_number0(item_number0_p0),
	.o_item_number1(item_number1_p0),
	.o_item_number2(item_number2_p0),
	.o_item_number3(item_number3_p0),
	.o_item_number4(item_number4_p0),
	.o_item_number5(item_number5_p0),
	.o_item_number6(item_number6_p0)
);

// P1 Item Number Decoder
ItemNumberDecoder item_number_decoder_p1(
	.i_item0(item_column_p1[0]),
	.i_item1(item_column_p1[1]),
	.i_item2(item_column_p1[2]),
	.i_item3(item_column_p1[3]),
	.i_item4(item_column_p1[4]),
	.i_item5(item_column_p1[5]),
	.o_item_number0(item_number0_p1),
	.o_item_number1(item_number1_p1),
	.o_item_number2(item_number2_p1),
	.o_item_number3(item_number3_p1),
	.o_item_number4(item_number4_p1),
	.o_item_number5(item_number5_p1),
	.o_item_number6(item_number6_p1)
);

always @(posedge clk or negedge rst_n) begin
	if (!rst_n) begin
		start_r <= 1'b0;
	end
	else begin
		start_r <= start_w;
	end
end

endmodule
