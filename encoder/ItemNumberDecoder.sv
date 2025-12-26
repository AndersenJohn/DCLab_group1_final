// Count Item Number Module

module ItemNumberDecoder (
	input [3:0]  i_item0,
	input [3:0]  i_item1,
	input [3:0]  i_item2,
	input [3:0]  i_item3,
	input [3:0]  i_item4,
	input [3:0]  i_item5,

	output [2:0] o_item_number0,
	output [2:0] o_item_number1,
	output [2:0] o_item_number2,
	output [2:0] o_item_number3,
	output [2:0] o_item_number4,
	output [2:0] o_item_number5,
	output [2:0] o_item_number6


);

// ===== Registers & Wires =====
logic [2:0] item_number0;
logic [2:0] item_number1;
logic [2:0] item_number2;
logic [2:0] item_number3;
logic [2:0] item_number4;
logic [2:0] item_number5;
logic [2:0] item_number6;


// ===== Output Assignments =====
assign o_item_number0 = item_number0;
assign o_item_number1 = item_number1;
assign o_item_number2 = item_number2;
assign o_item_number3 = item_number3;
assign o_item_number4 = item_number4;
assign o_item_number5 = item_number5;
assign o_item_number6 = item_number6;

// ===== Logic Assignments =====
always@(*) begin
	item_number0 = (i_item0[3] & (i_item0[2:0] == 3'd0)) + (i_item1[3] & (i_item1[2:0] == 3'd0)) + (i_item2[3] & (i_item2[2:0] == 3'd0)) + (i_item3[3] & (i_item3[2:0] == 3'd0)) + (i_item4[3] & (i_item4[2:0] == 3'd0)) + (i_item5[3] & (i_item5[2:0] == 3'd0));
	item_number1 = (i_item0[3] & (i_item0[2:0] == 3'd1)) + (i_item1[3] & (i_item1[2:0] == 3'd1)) + (i_item2[3] & (i_item2[2:0] == 3'd1)) + (i_item3[3] & (i_item3[2:0] == 3'd1)) + (i_item4[3] & (i_item4[2:0] == 3'd1)) + (i_item5[3] & (i_item5[2:0] == 3'd1));
	item_number2 = (i_item0[3] & (i_item0[2:0] == 3'd2)) + (i_item1[3] & (i_item1[2:0] == 3'd2)) + (i_item2[3] & (i_item2[2:0] == 3'd2)) + (i_item3[3] & (i_item3[2:0] == 3'd2)) + (i_item4[3] & (i_item4[2:0] == 3'd2)) + (i_item5[3] & (i_item5[2:0] == 3'd2));
	item_number3 = (i_item0[3] & (i_item0[2:0] == 3'd3)) + (i_item1[3] & (i_item1[2:0] == 3'd3)) + (i_item2[3] & (i_item2[2:0] == 3'd3)) + (i_item3[3] & (i_item3[2:0] == 3'd3)) + (i_item4[3] & (i_item4[2:0] == 3'd3)) + (i_item5[3] & (i_item5[2:0] == 3'd3));
	item_number4 = (i_item0[3] & (i_item0[2:0] == 3'd4)) + (i_item1[3] & (i_item1[2:0] == 3'd4)) + (i_item2[3] & (i_item2[2:0] == 3'd4)) + (i_item3[3] & (i_item3[2:0] == 3'd4)) + (i_item4[3] & (i_item4[2:0] == 3'd4)) + (i_item5[3] & (i_item5[2:0] == 3'd4));
	item_number5 = (i_item0[3] & (i_item0[2:0] == 3'd5)) + (i_item1[3] & (i_item1[2:0] == 3'd5)) + (i_item2[3] & (i_item2[2:0] == 3'd5)) + (i_item3[3] & (i_item3[2:0] == 3'd5)) + (i_item4[3] & (i_item4[2:0] == 3'd5)) + (i_item5[3] & (i_item5[2:0] == 3'd5));
	item_number6 = (i_item0[3] & (i_item0[2:0] == 3'd6)) + (i_item1[3] & (i_item1[2:0] == 3'd6)) + (i_item2[3] & (i_item2[2:0] == 3'd6)) + (i_item3[3] & (i_item3[2:0] == 3'd6)) + (i_item4[3] & (i_item4[2:0] == 3'd6)) + (i_item5[3] & (i_item5[2:0] == 3'd6));
end


endmodule

