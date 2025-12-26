// 純combinational，不存value，Top自己存

module Bullet_Item_Gen (
	input        i_clk,
	input        i_rst_n,
	input [3:0]  i_time,
	input [2:0]  i_hp_p0,
	input [2:0]  i_hp_p1,
	input [3:0]  i_bullet_num,
	output [7:0] o_bullet_bitmap,
	output [2:0]	 o_item1_p0,
	output [2:0]	 o_item2_p0,
	output [2:0]	 o_item3_p0,
	output [2:0]	 o_item4_p0,
	output [2:0]	 o_item5_p0,
	output [2:0]	 o_item6_p0,
	output [2:0]	 o_item1_p1,
	output [2:0]	 o_item2_p1,
	output [2:0]	 o_item3_p1,
	output [2:0]	 o_item4_p1,
	output [2:0]	 o_item5_p1,
	output [2:0]	 o_item6_p1
	
);

// ===== parameters =====
logic [7:0] random_bitmap [0:7];
//  = {
// 	8'b01101001, // 0
// 	8'b10000101, // 1
// 	8'b01010110, // 2
// 	8'b01011001, // 3
// 	8'b10100101, // 4
// 	8'b01100011, // 5
// 	8'b10010001, // 6
// 	8'b10011100  // 7
// };
assign random_bitmap[0] = 8'b01101001;
assign random_bitmap[1] = 8'b10110101;
assign random_bitmap[2] = 8'b01010110;
assign random_bitmap[3] = 8'b01011001;
assign random_bitmap[4] = 8'b10100101;
assign random_bitmap[5] = 8'b01101011;
assign random_bitmap[6] = 8'b10010101;
assign random_bitmap[7] = 8'b10011100;

// ===== Logic Assignments =====
// assign o_bullet_bitmap[1:0] = random_bitmap[i_time[2:0]][7:6];
// assign o_bullet_bitmap[3:2] = (i_bullet_num == 4'd4 || i_bullet_num == 4'd8) ? random_bitmap[i_time[2:0]][5:4] : 2'b00;
// assign o_bullet_bitmap[7:4] = (i_bullet_num == 4'd8) ? random_bitmap[i_time[2:0]][3:0] : 4'b0000;
assign o_bullet_bitmap[3:0] = random_bitmap[i_time[2:0]][7:4];
assign o_bullet_bitmap[5:4] = (i_bullet_num == 4'd6 || i_bullet_num == 4'd8) ? random_bitmap[i_time[2:0]][3:2] : 2'b00;
assign o_bullet_bitmap[7:6] = (i_bullet_num == 4'd8) ? random_bitmap[i_time[2:0]][1:0] : 2'b00;

assign o_item1_p0 = (i_hp_p0 + i_hp_p1 + i_time[2:0] == 3'd7) ? 3'd6 : i_hp_p0 + i_hp_p1 + i_time[2:0];
assign o_item2_p0 = (i_hp_p0 + i_time[2:0] == 3'd7) ? 3'd6 : i_hp_p0 + i_time[2:0];
assign o_item3_p0 = (i_hp_p1 + i_time[2:0] == 3'd7) ? 3'd6 : i_hp_p1 + i_time[2:0];
assign o_item4_p0 = (i_time[2:0] + (i_hp_p1 >> 1) == 3'd7) ? 3'd6 : i_time[2:0] + (i_hp_p1 >> 1);
assign o_item5_p0 = (i_time[2:0] + (i_hp_p0 >> 1) == 3'd7) ? 3'd6 : i_time[2:0] + (i_hp_p0 >> 1);
assign o_item6_p0 = (i_time[2:0] + 3'd3 == 3'd7) ? 3'd6 : i_time[2:0] + 3'd3;

assign o_item1_p1 = (i_hp_p0 + i_hp_p1 + i_time[2:0] + 3'd1 == 3'd7) ? 3'd6 : i_hp_p0 + i_hp_p1 + i_time[2:0] + 3'd1;
assign o_item2_p1 = (i_hp_p0 + i_time[2:0] + 3'd2 == 3'd7) ? 3'd6 : i_hp_p0 + i_time[2:0] + 3'd2;
assign o_item3_p1 = (i_hp_p1 + i_time[2:0] + 3'd3 == 3'd7) ? 3'd6 : i_hp_p1 + i_time[2:0] + 3'd3;
assign o_item4_p1 = (i_time[2:0] + (i_hp_p0 << 1) + 3'd1 == 3'd7) ? 3'd6 : i_time[2:0] + (i_hp_p0 << 1) + 3'd1;
assign o_item5_p1 = (i_time[2:0] + (i_hp_p1 << 1) + 3'd2 == 3'd7) ? 3'd6 : i_time[2:0] + (i_hp_p1 << 1) + 3'd2;
assign o_item6_p1 = (i_time[2:0] + 3'd5 == 3'd7) ? 3'd6 : i_time[2:0] + 3'd5;
 
endmodule

