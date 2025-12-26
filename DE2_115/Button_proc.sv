module Button_proc (
	input   i_clk,
	input   i_rst_n,
	input   i_exist,
	input   i_sparkle,
	input   i_button,
	output  o_button,
	output  o_select
);

parameter S_OFF = 1'b0;
parameter S_ON = 1'b1;

logic state_w, state_r;
logic select_w, select_r;

// assign i_button = 1'bz;
assign o_select = select_r;

always@(*) begin
	select_w = 1'b0;
	state_w = state_r;
	case (state_r)
		S_OFF: begin
			o_button = i_exist;
			if (!i_button) begin
				state_w = S_ON;
			end
			else begin
				state_w = S_OFF;
			end
		end
		S_ON: begin
			o_button = i_sparkle & i_exist;
			if (i_button) begin
				state_w = S_OFF;
				select_w = 1'b1;
			end
			else begin
				state_w = S_ON;
			end
		end
	endcase
end

always_ff @(posedge i_clk or negedge i_rst_n) begin
	if (!i_rst_n) begin
		state_r <= S_OFF;
		select_r <= 1'b0;
	end
	else begin
		state_r <= state_w;
		select_r <= select_w;
	end
end

endmodule

module Magnetic_Reed_Switch_Proc (
	input   i_clk,
	input   i_rst_n,
	input   i_switch,
	output  o_switch
);

parameter CNT_N = 50000000;

logic [31:0] counter;
logic switch_stable;
logic switch_d;

always_ff @(posedge i_clk or negedge i_rst_n) begin
	if (!i_rst_n) begin
		counter <= 32'd0;
		switch_stable <= 1'b0;
	end
	else begin
		if (i_switch) begin
			switch_stable <= 1'b1;
			counter <= CNT_N;
		end
		else begin
			if (counter > 0) begin
				counter <= counter - 1;
				switch_stable <= 1'b1;
			end
			else begin
				switch_stable <= 1'b0;
			end
		end
	end
end

always_ff @(posedge i_clk or negedge i_rst_n) begin
	if (!i_rst_n) begin
		switch_d <= 1'b0;
	end
	else begin
		switch_d <= switch_stable;
	end
end

assign o_switch = switch_stable & ~switch_d;

endmodule
