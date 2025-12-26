// Trigger Shock 0.5s Generater Module

module Trigger_Shock_Counter (
	input        i_clk,
	input        i_rst_n,
	input		 i_shock,
	output       o_trigger_shock_halfsecond
);

// ===== State Definition =====
localparam S_IDLE       = 1'b0;
localparam S_SHOCKING   = 1'b1;

// ===== Registers & Wires =====
logic [24:0] time_w, time_r;
logic        state_w, state_r;

// ===== Output Assignments =====
assign o_trigger_shock_halfsecond = state_r;

// ===== Logic Assignments =====
always @(*) begin
	// default
	time_w = time_r;
	state_w = state_r;
	case (state_r)
		S_IDLE: begin
			time_w = 25'd0;
			if (i_shock) begin
				state_w = S_SHOCKING;
			end
		end
		S_SHOCKING: begin
			time_w = time_r + 4'd1;
			if (time_r[24]) begin
				time_w = 25'd0;
				state_w = S_IDLE;
			end
		end
	endcase
end

// ===== Sequential Circuits =====
always_ff @(posedge i_clk or negedge i_rst_n) begin
	// reset
	if (!i_rst_n) begin
		time_r <= 25'd0;
		state_r <= S_IDLE;
	end
	else begin
		time_r <= time_w;
		state_r <= state_w;
	end
end

endmodule

