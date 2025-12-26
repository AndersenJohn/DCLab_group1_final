module Game_PC_Interface (
    input        clk,
    input        rst_n,
    
    // --- 來自 Game_logic 的所有 Outputs ---
    input [2:0] i_hp_p0,
    input [2:0] i_hp_p1,
    input [3:0] i_bullet_bitmap_ptr,
    input [3:0] i_total_bullet,
    input [3:0] i_total_bullet_remaining,
    input [2:0] i_bullet_filled,
    input [2:0] i_bullet_empty,
    input       i_bullet_report_valid,
    input       i_bullet_report,
    input [2:0] i_report_idx,
    input [1:0] i_winner,
    // item positions P0
    input [3:0] i_item_column_p0_0, i_item_column_p0_1, i_item_column_p0_2,
    input [3:0] i_item_column_p0_3, i_item_column_p0_4, i_item_column_p0_5,
    // item positions P1
    input [3:0] i_item_column_p1_0, i_item_column_p1_1, i_item_column_p1_2,
    input [3:0] i_item_column_p1_3, i_item_column_p1_4, i_item_column_p1_5,
    // state & player
    input [3:0] i_state,
    input       i_playerA,
    input       i_playerB,
    // bullet bitmap & active
    input [7:0] i_bullet_bitmap,
    input       i_saw_active,
    input       i_reverse_active,
    input       i_handcuff_active,

    // --- 對接 uart_tx 的控制介面 ---
    input        i_tx_busy,      // UART 忙碌中
    output logic o_tx_start,     // 觸發 UART 傳送
    output logic [7:0] o_tx_data,// 要傳送的 Byte
    
    // --- 完成訊號 ---
    output logic o_tx_done       
);

    // 定義關鍵狀態 (狀態改變時觸發傳送)
    localparam S_LOAD       = 4'd1;
    localparam S_ITEM_PROC  = 4'd4;
    localparam S_SHOOT_PROC = 4'd7;
    localparam S_DONE       = 4'd8;

    // 傳送狀態機參數
    typedef enum logic [1:0] {S_IDLE, S_SEND, S_WAIT} fsm_t;
    fsm_t state_r, state_w;

    // 內部訊號
    logic [3:0] tx_byte_cnt;        // 計數器 0~13
    logic [7:0] packet_buffer [0:13]; 
    logic       trigger_send;

    // *** 新增：用於延遲一個 Cycle 的訊號 ***
    logic       condition_match_d; 

    // ===============================================================
    // 1. 偵測狀態 & 打包數據 (已修改：延遲一週期打包)
    // ===============================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            trigger_send      <= 1'b0;
            condition_match_d <= 1'b0; // Reset delay reg
            for(int k=0; k<14; k++) packet_buffer[k] <= 8'd0;
        end else begin
            // A. 第一步：判斷當前狀態是否符合條件，並存入 Register (造成 1 Cycle Delay)
            if ( i_state == S_LOAD || i_state == S_ITEM_PROC || i_state == S_SHOOT_PROC ) begin
                condition_match_d <= 1'b1;
            end else begin
                condition_match_d <= 1'b0;
            end

            // B. 第二步：根據「上一週期」的判斷結果 (condition_match_d) 來打包數據
            //    這樣 packet_buffer 抓到的會是 "狀態成立後下一個 Cycle" 的數據
            if (condition_match_d) begin 
                
                trigger_send <= 1'b1; // 發出觸發訊號
                
                // === 數據打包 (此時捕捉的是 Delay 後當下的 Input) ===
                packet_buffer[0]  <= 8'hA5; // Header
                packet_buffer[1]  <= {i_winner, i_state, i_playerA, i_playerB};
                packet_buffer[2]  <= {i_saw_active, i_reverse_active, i_handcuff_active, i_bullet_report_valid, i_bullet_report, i_report_idx};
                packet_buffer[3]  <= {i_hp_p0, 1'b0, i_hp_p1, 1'b0};
                packet_buffer[4]  <= {i_total_bullet, i_total_bullet_remaining};
                packet_buffer[5]  <= {i_bullet_filled, 1'b0, i_bullet_empty, 1'b0};
                packet_buffer[6]  <= {i_bullet_bitmap_ptr, 4'b0};
                packet_buffer[7]  <= i_bullet_bitmap;
                // Items P0
                packet_buffer[8]  <= {i_item_column_p0_0, i_item_column_p0_1};
                packet_buffer[9]  <= {i_item_column_p0_2, i_item_column_p0_3};
                packet_buffer[10] <= {i_item_column_p0_4, i_item_column_p0_5};
                // Items P1
                packet_buffer[11] <= {i_item_column_p1_0, i_item_column_p1_1};
                packet_buffer[12] <= {i_item_column_p1_2, i_item_column_p1_3};
                packet_buffer[13] <= {i_item_column_p1_4, i_item_column_p1_5};

            end else begin
                trigger_send <= 1'b0;
            end
        end
    end

    // ===============================================================
    // 2. 發送狀態機 (Sequential Part) - 保持不變
    // ===============================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_r     <= S_IDLE;
            tx_byte_cnt <= 4'd0;
            o_tx_done   <= 1'b0;
        end else begin
            state_r <= state_w; // 更新狀態
            
            o_tx_done <= 1'b0;

            // Counter Logic
            if (state_r == S_IDLE) begin
                tx_byte_cnt <= 4'd0;
            end
            else if (state_r == S_WAIT && !i_tx_busy) begin
                // 當前 Byte 傳送完畢
                if (tx_byte_cnt == 4'd13) begin
                    o_tx_done <= 1'b1;
                    tx_byte_cnt <= 4'd0;
                end else begin
                    tx_byte_cnt <= tx_byte_cnt + 1'b1;
                end
            end
        end
    end

    // ===============================================================
    // 3. 發送狀態機 (Combinational Part) - 保持不變
    // ===============================================================
    always_comb begin
        state_w    = state_r; 
        o_tx_start = 1'b0;
        o_tx_data  = 8'd0;

        case (state_r)
            S_IDLE: begin
                // trigger_send 在 Delay 後才會拉起，這裡會正常接收
                if (trigger_send) state_w = S_SEND;
            end

            S_SEND: begin
                o_tx_data  = packet_buffer[tx_byte_cnt];
                o_tx_start = 1'b1;
                state_w = S_WAIT; 
            end

            S_WAIT: begin
                o_tx_start = 1'b0;
                
                if (!i_tx_busy) begin
                    if (tx_byte_cnt == 4'd13) 
                        state_w = S_IDLE;
                    else
                        state_w = S_SEND;
                end
            end
        endcase
    end

endmodule