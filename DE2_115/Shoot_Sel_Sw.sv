module Shoot_Sel_Switch (
	input   i_clk,
	input   i_rst_n,
	input   i_playerA,
	input   i_to_p0,
	input   i_to_p1,
	input   i_trigger,
	input   i_sparkle,
	inout   o_to_p0,
	inout   o_to_p1,
	output  o_shoot_select
);

parameter S_IDLE = 2'd0;
parameter S_TO_P0 = 2'd1;
parameter S_TO_P1 = 2'd2;

logic [1:0] state_w, state_r;
logic shoot_select_w, shoot_select_r;

assign o_to_p0	 = state_r[0] & i_sparkle;
assign o_to_p1	 = state_r[1] & i_sparkle;
assign shoot_select_w = (i_playerA & state_r[0]) | ((!i_playerA) & state_r[1]);
assign o_shoot_select = shoot_select_r;

always @(*) begin
	state_w = state_r;
	case (state_r)
		S_IDLE: begin
			if (i_to_p0) begin
				state_w = S_TO_P0;
			end
			else if (i_to_p1) begin
				state_w = S_TO_P1;
			end
		end
		S_TO_P0: begin
			if (i_trigger) begin
				state_w = S_IDLE;
			end
			else if (i_to_p1) begin
				state_w = S_TO_P1;
			end
		end
		S_TO_P1: begin
			if (i_trigger) begin
				state_w = S_IDLE;
			end
			else if (i_to_p0) begin
				state_w = S_TO_P0;
			end
		end
		default: state_w = S_IDLE;
	endcase
end

always_ff @(posedge i_clk or negedge i_rst_n) begin
	if (!i_rst_n) begin
		state_r <= S_IDLE;
		shoot_select_r <= 1'b0;
	end
	else begin
		state_r <= state_w;
		shoot_select_r <= shoot_select_w;
	end
end

endmodule
