from sb3_contrib import MaskablePPO
model = MaskablePPO.load("buckshot_final.zip")
print(model.policy.mlp_extractor.policy_net[0].weight.shape)
