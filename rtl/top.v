`timescale 1ns/1ps

module top (
    input wire clk,
    input wire reset,
    input wire signed [15:0] input_sample,
    input wire sample_valid,
    output reg uart_tx,
    output reg anomaly_led
);

    reg signed [15:0] fir_coeffs [0:100];

    initial begin
        $readmemh("coeffs.hex", fir_coeffs);
    end

    reg signed [15:0] weight1 = 16'sd232;  
    reg signed [15:0] weight2 = 16'sd195;  
    reg signed [15:0] bias    = -16'sd161; 

    reg signed [15:0] shift_reg [0:100];
    reg signed [15:0] fir_out;
    reg signed [31:0] acc;
    reg [6:0] filter_counter;
    reg filter_busy;
    reg fir_valid;

    integer i;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            for (i = 0; i < 101; i = i + 1) shift_reg[i] <= 0;
            fir_out <= 0;
            acc <= 0;
            filter_counter <= 0;
            filter_busy <= 0;
            fir_valid <= 0;
        end else begin
            fir_valid <= 0;
            
            if (sample_valid && !filter_busy) begin
                for (i = 100; i > 0; i = i - 1)
                    shift_reg[i] <= shift_reg[i-1];
                shift_reg[0] <= input_sample;
                
                filter_busy <= 1'b1;
                filter_counter <= 0;
                acc <= 0;
            end else if (filter_busy) begin
                acc <= acc + (shift_reg[filter_counter] * fir_coeffs[filter_counter]);
                filter_counter <= filter_counter + 1;
                
                if (filter_counter == 100) begin
                    filter_busy <= 1'b0;
                    fir_out <= acc[30:15]; 
                    fir_valid <= 1'b1;
                end
            end
        end
    end

    reg signed [15:0] max_val, mean_val;
    reg signed [31:0] score;
    reg anomaly;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            max_val <= 0;
            mean_val <= 0;
            score <= 0;
            anomaly <= 0;
            anomaly_led <= 0;
        end else if (fir_valid) begin
            max_val <= (fir_out > 0) ? fir_out : -fir_out;
            mean_val <= ((fir_out > 0) ? fir_out : -fir_out) >> 1; 
            
            score <= (weight1 * max_val) + (weight2 * mean_val) + (bias <<< 15);
            
            anomaly <= (score > 0) ? 1'b1 : 1'b0;
            anomaly_led <= anomaly;
        end
    end

    reg [9:0] tx_shift;
    reg [3:0] tx_bit;
    reg tx_busy;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            uart_tx <= 1'b1;
            tx_busy <= 1'b0;
            tx_bit <= 0;
            tx_shift <= 10'b1111111111;
        end else begin
            if (fir_valid && !tx_busy) begin
                tx_shift <= {1'b1, 7'b0, anomaly, 1'b0}; 
                tx_busy <= 1'b1;
                tx_bit <= 0;
            end else if (tx_busy) begin
                uart_tx <= tx_shift[0];
                tx_shift <= {1'b1, tx_shift[9:1]};
                tx_bit <= tx_bit + 1;
                if (tx_bit == 9) begin
                    tx_busy <= 1'b0;
                end
            end
        end
    end

endmodule
