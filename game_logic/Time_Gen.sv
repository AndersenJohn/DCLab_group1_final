// Time Generater Module

module Time_Gen (
	input        i_clk,
	input        i_rst_n,
	output [3:0] o_time


);

// ===== Registers & Wires =====
logic [3:0] time_w, time_r;

// ===== Output Assignments =====
assign o_time = time_r;

// ===== Logic Assignments =====
assign time_w = time_r + 4'd1;

// ===== Sequential Circuits =====
always_ff @(posedge i_clk or negedge i_rst_n) begin
	// reset
	if (!i_rst_n) begin
		time_r <= 4'd0;
	end
	else begin
		time_r <= time_w;
	end
end

endmodule

