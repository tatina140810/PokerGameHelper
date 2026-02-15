from poker.montecarlo import MonteCarloSimulation
from poker.card import Card
import time

def test_perf():
    sim = MonteCarloSimulation()
    hero = [Card('A', '♠'), Card('K', '♠')]
    board = [Card('2', '♥'), Card('7', '♦'), Card('Q', '♣')]
    
    print("Starting simulation (50,000 iterations)...")
    start = time.time()
    sim.run(hero, board, iterations=50000)
    end = time.time()
    
    duration = end - start
    print(f"Duration: {duration:.4f} seconds")

if __name__ == "__main__":
    test_perf()
