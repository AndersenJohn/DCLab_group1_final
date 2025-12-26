// Item Function Module

module Use_Item (
	input        i_clk,
	input        i_rst_n,
	input    	 i_use_item,
	input [2:0]  i_item,
	input [7:0]  i_bullet_bitmap,
	input [3:0]  i_bullet_bitmap_ptr,
	input [3:0]  i_hp_p1,
	input [3:0]  i_hp_p2,
	input 		 i_saw_active,
	input 		 i_reverse_active,
	input 		 i_handcuff_active,
	input		 i_playerA,
	input		 i_playerB,

	// Phone and Magnifier Report
	input [3:0]  i_total_bullet_remaining,
	input [3:0]  i_time,
	input [3:0]  i_total_bullet,
	output 		 o_bullet_report_valid,
	output 		 o_bullet_report,
	output [2:0] o_report_idx,

	// Cigarette and Medicine Report
	output [3:0] o_hp_p1_report,
	output [3:0] o_hp_p2_report,

	// saw
	output       o_saw_active,

	// beer
	output [3:0]  o_bitmap_ptr,

	// reverse
	output       o_reverse_active,

	// handcuff
	output       o_handcuff_active

	// gun (do nothing)
	// (bullet <= 3) => last
	// else => last 3 random
);

parameter use_magnifier = 3'd0;
parameter use_cigarette = 3'd1;
parameter use_handcuff = 3'd2;
parameter use_saw = 3'd3;
parameter use_beer = 3'd4;
parameter use_phone = 3'd5;
parameter use_reverse = 3'd6;
parameter use_gun = 3'd7;

// ===== Registers & Wires =====
logic 	 bullet_report_valid;
logic 	 bullet_report;
logic [2:0] report_idx;
logic [3:0] hp_p1_report;
logic [3:0] hp_p2_report;
logic       saw_active;
logic [3:0] bitmap_ptr;
logic       reverse_active;
logic       handcuff_active;
// ===== Logic Assignments =====
assign o_bullet_report_valid = bullet_report_valid;
assign o_bullet_report = bullet_report;
assign o_report_idx = report_idx;
assign o_hp_p1_report = hp_p1_report;
assign o_hp_p2_report = hp_p2_report;
assign o_saw_active = saw_active;
assign o_bitmap_ptr = bitmap_ptr;
assign o_reverse_active = reverse_active;
assign o_handcuff_active = handcuff_active;
// ===== Combinational Circuits =====
always @(*) begin
	// Default Values
	bullet_report_valid = 1'b0;
	bullet_report = 1'b0;
	report_idx = 3'b0;
	hp_p1_report = i_hp_p1;
	hp_p2_report = i_hp_p2;
	saw_active = i_saw_active;
	bitmap_ptr = i_bullet_bitmap_ptr;
	reverse_active = i_reverse_active;
	handcuff_active = i_handcuff_active;
	// Use Item
	if (i_use_item) begin
		case (i_item)
			use_magnifier: begin
				bullet_report_valid = 1'b1;
				bullet_report = i_bullet_bitmap[i_bullet_bitmap_ptr];
				report_idx = 3'd0; // for magnifier, idx is 0
			end
			use_phone: begin
				bullet_report_valid = 1'b1;
				if (i_total_bullet_remaining <= 4'd3) begin
					bullet_report = i_bullet_bitmap[i_total_bullet - 4'b1];
					report_idx = i_total_bullet - i_bullet_bitmap_ptr - 4'b1;
				end
				else begin
					bullet_report = i_bullet_bitmap[i_total_bullet - i_time[1:0] - 4'b1];
					report_idx = i_total_bullet - i_time[1:0] - 4'b1 - i_bullet_bitmap_ptr;
				end
				
			end
			use_cigarette: begin
				if (i_hp_p1 < 3'd4 && ~i_playerA)
					hp_p1_report = i_hp_p1 + 3'd1;
				if (i_hp_p2 < 3'd4 && i_playerA)
					hp_p2_report = i_hp_p2 + 3'd1;
			end
			use_saw: begin
				saw_active = 1'b1;
			end
			use_beer: begin
				bitmap_ptr = i_bullet_bitmap_ptr + 4'd1;
			end
			use_reverse: begin
				reverse_active = 1'b1;
			end
			use_handcuff: begin
				handcuff_active = 1'b1;
			end
			default: begin
				// do nothing for phone 晚點做
				// gun do nothing
			end
		endcase
	end
end

endmodule

