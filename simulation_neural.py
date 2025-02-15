import argparse
import yaml

from DiffList.DiffManager import DiffManager

from util_functions import *
from conf import *
from LastFM_util_functions import *
from YahooExp_util_functions import *
from L2RRewardManager import L2RRewardManager
from lib.NeuralUCB import NeuralUCBAlgorithm
from lib.NeuralLinear import NeuralLinearAlgorithm
from lib.NeuralLinUCB import NeuralLinUCBAlgorithm
from lib.NeuralLinearLikelihoodMatching import NeuralLinearLikelihoodMatchingAlgorithm


def generate_algorithms(alg_dict, W, system_params):
    gen = alg_dict["general"] if "general" in alg_dict and alg_dict["general"] else {}
    algorithms = {}
    diffLists = DiffManager()
    for i in alg_dict["specific"]:
        print("")
        print(str(i))
        try:
            tmpDict = globals()["create" + i + "Dict"](alg_dict["specific"][i] if alg_dict["specific"][i] else {}, gen,
                                                       W, system_params)
        except KeyError:
            tmpDict = createBaseAlgDict(alg_dict["specific"][i] if alg_dict["specific"][i] else {}, gen, W,
                                        system_params)
        try:
            algorithms[i] = globals()[i + "Algorithm"](tmpDict)
        except KeyError:
            raise NotImplementedError(i + " not currently implemented")
        diffLists.add_algorithm(i, algorithms[i].getEstimateSettings())
    # print algorithms
    return algorithms, diffLists


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulation for Neural Bandit Algorithms")
    parser.add_argument("--config", dest="config", default="C:/Users/wbw/PycharmProjects/BanditLib"
                                                           "/SimulationConfigNeuralLinearLikelihoodMatching.yaml", help="yaml config file")
    args = parser.parse_args()

    with open(args.config, "r") as ymlfile:
        cfg = yaml.load(ymlfile,Loader=yaml.FullLoader)
    gen = cfg["general"] if "general" in cfg else {}
    context_dimension = gen["context_dimension"] if "context_dimension" in gen else 136
    system_params = {"context_dim": context_dimension, "n_users": 1}
    algorithms, diffLists = generate_algorithms(cfg["alg"], None, system_params)
    rewardManagerDict = {}
    rewardManagerDict["context_dimension"] = gen["context_dimension"]

    rewardManagerDict["k"] = gen["k"]
    if gen["dataset"] == "Web10K":
        rewardManagerDict["address"] = "D:/OneDrive - University of Virginia/neural bandit algorithm/MSLR-WEB10K/Fold1/"
        rewardManagerDict["save_address"] = "./Results/Web10KResults/"
        rewardManagerDict["context_dimension"] = 136
    if gen["dataset"] == "YahooL2R":
        rewardManagerDict["address"] = "../datasets/Yahoo_hcdm/Fold1/"
        rewardManagerDict["save_address"] = "./Results/YahooL2RResults/"
        rewardManagerDict["context_dimension"] = 700

    print("Running for dataset {}".format(gen["dataset"]))

    experiment = L2RRewardManager(arg_dict=rewardManagerDict)
    experiment.runAlgorithms(algorithms, diffLists)
