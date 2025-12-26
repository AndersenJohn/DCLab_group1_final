module AI_to_Top (
    input              clk,
    input              rst_n,
    input  [3:0]       action,       // 0~9: Valid Action, 15: Idle
    input  [3:0]       item_column0,
    input  [3:0]       item_column1,
    input  [3:0]       item_column2,
    input  [3:0]       item_column3,
    input  [3:0]       item_column4,
    input  [3:0]       item_column5,
    output [5:0]       o_item_select,
    output             o_item_shoot,
    output             o_shoot_trigger,
    output             o_shoot_select
);

    wire [2:0] target_item_id;
    assign target_item_id = action[2:0] - 3'd2; 

    // Internal Signals
    logic [5:0] item_select_w, item_select_r;
    logic item_shoot_w, item_shoot_r;
    logic shoot_trigger_w, shoot_trigger_r;
    logic shoot_select_w, shoot_select_r;

    // Output Assignments
    assign o_item_select   = item_select_r;
    assign o_item_shoot    = item_shoot_r;
    assign o_shoot_trigger = shoot_trigger_r;
    assign o_shoot_select  = shoot_select_r;

    // ===============================================================
    // Combinational Logic
    // ===============================================================
    always @(*) begin
        item_select_w   = 6'b000000;
        item_shoot_w    = 1'b0;
        shoot_trigger_w = 1'b0;
        shoot_select_w  = 1'b0;

        case (action)
            4'd0: begin
                shoot_trigger_w = 1'b1;
                shoot_select_w  = 1'b1; // 1: Enemy
            end
            4'd1: begin
                shoot_trigger_w = 1'b1;
                shoot_select_w  = 1'b0; // 0: Self
            end

            4'd2, 4'd3, 4'd4, 4'd5, 4'd6, 4'd7, 4'd8: begin
                if (item_column0[2:0] == target_item_id && item_column0[3])
                    item_select_w = 6'b000001;
                else if (item_column1[2:0] == target_item_id && item_column1[3])
                    item_select_w = 6'b000010;
                else if (item_column2[2:0] == target_item_id && item_column2[3])
                    item_select_w = 6'b000100;
                else if (item_column3[2:0] == target_item_id && item_column3[3])
                    item_select_w = 6'b001000;
                else if (item_column4[2:0] == target_item_id && item_column4[3])
                    item_select_w = 6'b010000;
                else if (item_column5[2:0] == target_item_id && item_column5[3])
                    item_select_w = 6'b100000;
            end
            4'd9: begin
                item_shoot_w = 1'b1;
            end
        endcase
    end
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            item_select_r   <= 6'b0;
            item_shoot_r    <= 1'b0;
            shoot_trigger_r <= 1'b0;
            shoot_select_r  <= 1'b0;
        end
        else begin
            item_select_r   <= item_select_w;
            item_shoot_r    <= item_shoot_w;
            shoot_trigger_r <= shoot_trigger_w;
            shoot_select_r  <= shoot_select_w;
        end
    end

endmodule