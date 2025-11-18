from buckshot_env import BuckshotEnv
from main import show

env = BuckshotEnv()
obs, info = env.reset()

show(env.gs)
print("State:", obs)

for a in range(9):
    print(f"\n===== Try Action {a} =====")
    obs, reward, done, trunc, info = env.step(a)
    print("Reward:", reward)
    if done:
        print("Game finished.")
        break
