// Previne uma janela de console adicional no Windows em modo release.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    money_fronts_lib::run();
}
