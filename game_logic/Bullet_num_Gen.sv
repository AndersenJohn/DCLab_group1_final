// Top 中的子彈數量依循 o1 -> 02 -> o3 -> o4 -> o2 -> o3 -> o4 -> o2 -> ...

module Bullet_num_Gen (
	input        i_clk,
	input        i_rst_n,
	input 		 i_start,
	input [3:0]  i_time,
	output [3:0]  o1,	// 4
	output [3:0]  o2,   // 4, 6
	output [3:0]  o3,	// 4, 6, 8
	output [3:0]  o4	// 4, 6, 8


);

// ===== Registers & Wires =====
logic o2_w, o2_r;
logic [3:0] o3_w, o3_r;
logic [3:0] o4_w, o4_r;

// ===== Output Assignments =====
assign o1 = 4'd4;
assign o2 = {2'b01, o2_r, 1'b0};
assign o3 = o3_r;
assign o4 = o4_r;

// ===== Logic Assignments =====
assign o2_w = (i_start) ? (i_time[0]) ? 1'b0 : 1'd1 : o2_r;
assign o3_w = (i_start) ? (i_time[0]) ? (i_time[1]) ? 4'd8 : 4'd6 : (i_time[1]) ? 4'd8 : 4'd4 : o3_r;
assign o4_w = (i_start) ? (i_time[3]) ? 4'd8 : (i_time[2]) ? 4'd6 : 4'd4 : o4_r;

// ===== Sequential Circuits =====
always_ff @(posedge i_clk or negedge i_rst_n) begin
	// reset
	if (!i_rst_n) begin
		o2_r <= 1'b0;
		o3_r <= 4'd4;
		o4_r <= 4'd4;
	end
	else begin
		o2_r <= o2_w;
		o3_r <= o3_w;
		o4_r <= o4_w;
	end
end

endmodule

