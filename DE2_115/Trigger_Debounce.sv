module Trigger_Debounce (
	input  i_in,
	input  i_clk,
	input  i_rst_n,
	output o_trigger
);

parameter CNT_N = 50000000;
localparam CNT_BIT = $clog2(CNT_N+1);

logic o_debounced_r, o_debounced_w;
logic [CNT_BIT-1:0] counter_r, counter_w;

assign o_trigger = o_debounced_r;

always_comb begin
	if (counter_r == 0) begin
		counter_w = CNT_N;
	end
	else if (i_in == 1'b0) begin
		counter_w = counter_r - 1;
	end 
	else begin
		counter_w = CNT_N;
	end

	if (counter_r == 0) begin
		o_debounced_w = 1'b1;
	end 
	else begin
		o_debounced_w = 1'b0;
	end
end

always_ff @(posedge i_clk or negedge i_rst_n) begin
	if (!i_rst_n) begin
		o_debounced_r <= 1'b0;
		counter_r <= CNT_N;
	end else begin
		o_debounced_r <= o_debounced_w;
		counter_r <= counter_w;
	end
end

endmodule
