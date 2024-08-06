from ChessOptimizer.DataTransformer import get_newest_data, processAndCleanData
from ChessOptimizer.Optimizer.advanced import genetic_algorithm_optimizer

if __name__ == "__main__":
    original_src_folder = "src/original"
    processed_src_folder = "src/processed"
    get_newest_data(original_src_folder)
    processAndCleanData(original_src_folder, processed_src_folder)
    genetic_algorithm_optimizer(processed_src_folder)
