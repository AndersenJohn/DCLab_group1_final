// Time Generater Module

module Light_Gen (
	input        i_clk,
	input        i_rst_n,
	output       o_on,
	output 		 o_47Hz_sqrwave
);

// ===== Registers & Wires =====
logic [24:0] time_w, time_r;

// ===== Output Assignments =====
assign o_on = time_r[24];
assign o_47Hz_sqrwave = time_r[19];

// ===== Logic Assignments =====
assign time_w = time_r + 4'd1;

// ===== Sequential Circuits =====
always_ff @(posedge i_clk or negedge i_rst_n) begin
	// reset
	if (!i_rst_n) begin
		time_r <= 25'd0;
	end
	else begin
		time_r <= time_w;
	end
end

endmodule

