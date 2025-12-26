module uart_tx #(
    parameter CLK_FREQ = 50000000, // 你的時脈頻率 (DE2-115 是 50MHz)
    parameter BAUD_RATE = 115200   // 傳輸速度 (電腦端要設一樣)
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire       tx_start,    // 給一個 High Pulse 就會開始傳
    input  wire [7:0] tx_data,     // 要傳的那個 Byte
    output reg        tx_line,     // 接到 FPGA 實體腳位 UART_TXD
    output wire       tx_busy      // 1代表忙碌中
);

    // 計算傳一個 bit 需要數幾個 clock
    localparam CLK_PER_BIT = CLK_FREQ / BAUD_RATE;
    
    // 狀態定義
    localparam S_IDLE  = 0;
    localparam S_START = 1;
    localparam S_DATA  = 2;
    localparam S_STOP  = 3;

    reg [2:0] state;
    reg [15:0] clk_cnt; // 用來計時
    reg [2:0] bit_idx;  // 用來數傳到第幾個 bit
    reg [7:0] data_reg; // 暫存資料

    assign tx_busy = (state != S_IDLE);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state   <= S_IDLE;
            tx_line <= 1'b1; // UART 空閒時是高電位 (High)
            clk_cnt <= 0;
            bit_idx <= 0;
        end else begin
            case (state)
                // 1. 等待發送訊號
                S_IDLE: begin
                    tx_line <= 1'b1;
                    clk_cnt <= 0;
                    if (tx_start) begin
                        data_reg <= tx_data;
                        state    <= S_START;
                    end
                end
                
                // 2. 發送 Start Bit (拉低電位 1 個 bit 的時間)
                S_START: begin
                    tx_line <= 1'b0;
                    if (clk_cnt < CLK_PER_BIT - 1)
                        clk_cnt <= clk_cnt + 1;
                    else begin
                        clk_cnt <= 0;
                        state   <= S_DATA;
                        bit_idx <= 0;
                    end
                end
                
                // 3. 依序發送 8 個 Data Bits
                S_DATA: begin
                    tx_line <= data_reg[bit_idx]; // 傳送當前 bit
                    if (clk_cnt < CLK_PER_BIT - 1)
                        clk_cnt <= clk_cnt + 1;
                    else begin
                        clk_cnt <= 0;
                        if (bit_idx < 7)
                            bit_idx <= bit_idx + 1;
                        else
                            state <= S_STOP;
                    end
                end
                
                // 4. 發送 Stop Bit (拉高電位，結束傳輸)
                S_STOP: begin
                    tx_line <= 1'b1;
                    if (clk_cnt < CLK_PER_BIT - 1)
                        clk_cnt <= clk_cnt + 1;
                    else
                        state <= S_IDLE; // 回到待機
                end
            endcase
        end
    end
endmodule