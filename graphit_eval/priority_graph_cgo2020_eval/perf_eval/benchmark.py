#!/usr/bin/python
import argparse
import subprocess
import os
import shlex
import time
from threading import Timer

# maps to the specific binary name (except for GraphIt)
# wBFS is just DeltaStepping with delta set to 1

framework_app_lookup = {
    "greenmarl": {"pr": "pagerank", "sssp": "sssp", "bfs": "bfs", "cc": "cc"},
    "gapbs": {"ds": "delta_stepping", "ppsp":"ppsp", "astar":"astar", "wBFS":"wBFS"},
    "gapbs_prototype": { "ds": "delta_stepping", "ppsp":"ppsp", "wBFS":"wBFS"},
    "julienne":{"ds": "DeltaStepping", "ppsp":"PPSP", "astar":"Astar", "wBFS":"wBFS"},
    "galois": {"pr": "pagerank", "sssp": "sssp", "bfs": "bfs", "cc": "connectedcomponents", "bc": "betweennesscentrality", "astar": "astar", "ds": "deltastepping", "ppsp": "ppsp", "wBFS": "wBFS"},
    "ligra": {"pr": "PageRank", "sssp": "BellmanFord", "bfs": "BFS", "cc": "Components", "prd": "PageRankDelta", "cf": "CF", "bc": "BC"},
    "gemini": {"pr": "pagerank", "sssp": "sssp", "bfs": "bfs", "cc": "cc", "bc": "bc"},
    "graphit": {"pr": "pr", "sssp": "sssp", "bfs": "bfs", "cc": "cc", "prd": "prd", "cf": "cf", "ds": "sssp_delta_stepping", "ds_lazy" : "sssp_delta_stepping_lazy" ,"ppsp" : "ppsp_delta_stepping", "astar" : "astar", "wBFS" : "wBFS"},
    "grazelle": {"pr": "pr", "cc": "cc", "bfs": "bfs"},
    "polymer": {"pr": "numa-PageRank", "sssp": "numa-BellmanFord", "bfs": "numa-BFS", "cc": "numa-Components", "prd": "numa-PageRankDelta"}
}

#shared across all frameworks
wBFS_runtime_param_dict = {"socLive_rand1000" : 1, "road-usad_rand1000" : 1, "road-usad_origweights" : 1, "twitter_rand1000" : 1, "friendster": 1,  "webGraph_rand1000": 1, "friendster_rand1000": 1, "socLive_logn" : 1, "com_orkut_W": 1, "webGraph_logn": 1, "twitter_logn" : 1, "friendster_logn": 1}

# stores the runtime parameter for each application, on each graph for each framework
framework_app_graph_runtime_param_map = {
    "gapbs" : {"delta_stepping": {"socLive_rand1000" : 100, "road-usad_rand1000" : 10000, "road-usad_origweights" : 100000, "twitter_rand1000" : 8, "twitter_logn" : 1, "friendster": 2, "com_orkut_W": 1, "com_orkut_rand1000": 8, "webGraph_rand1000": 4, "friendster_rand1000": 4, "friendster_logn": 5, "germany" : 300000}, 
               "ppsp" : {"socLive_rand1000" : 50, "road-usad_rand1000" : 10000, "road-usad_origweights" : 100000,"twitter_rand1000" : 4, "com_orkut_W": 1, "com_orkut_rand1000": 8, "webGraph_rand1000": 16, "friendster_rand1000": 1, "germany" : 300000}, 
               "astar" : {"germany" : 300000, "massachusetts" : 35000, "monaco" : 35000, "road-usad_origweights" : 40000},
               "wBFS": wBFS_runtime_param_dict},

    "graphit" : {"sssp_delta_stepping": {"socLive_logn" : 1, "socLive_rand1000" : 100, "road-usad_rand1000" : 8000, "road-usad_origweights" : 40000, "twitter_rand1000" : 4, "twitter_logn" : 1, "com_orkut_W": 1, "com_orkut_rand1000": 8, "webGraph_rand1000":4, "webGraph_logn": 1,"friendster_rand1000": 2, "friendster_logn": 5, "germany":400000, "road-central-usa_origweights":400000},
                 "sssp_delta_stepping_lazy":{"socLive_rand1000" : 100, "road-usad_rand1000" : 4096, "road-usad_origweights" : 10000, "twitter_rand1000" : 4, "com_orkut_W": 4, "com_orkut_rand1000": 8, "webGraph_rand1000": 8, "friendster_rand1000": 2},
                 "ppsp_delta_stepping" : {"socLive_rand1000" : 50, "road-usad_rand1000" : 8000, "road-usad_origweights" : 40000, "twitter_rand1000" : 4, "com_orkut_W": 1, "com_orkut_rand1000": 8, "webGraph_rand1000":4, "friendster_rand1000": 1, "germany":400000, "road-central-usa_origweights":400000}, 
                 "astar" : {"germany" : 45000, "massachusetts" : 35000, "monaco" : 35000, "road-usad_origweights" : 40000, "road-central-usa_origweights":400000},
                 "wBFS": wBFS_runtime_param_dict},

    "gapbs_prototype" : {"delta_stepping": {"socLive_rand1000" : 100, "road-usad_rand1000" : 8000, "road-usad_origweights" : 40000, "twitter_rand1000" : 4, "friendster_rand1000": 2}, 
               "ppsp" : {"socLive_rand1000" : 50, "road-usad_rand1000" : 8000, "road-usad_origweights" : 40000, "twitter_rand1000" : 4, "friendster_rand1000": 1},
                         "wBFS": wBFS_runtime_param_dict},

    "julienne" : {"DeltaStepping": {"socLive_rand1000" : 100, "road-usad_rand1000" : 4096, "road-usad_origweights" : 10000, "germany" : 35000, "twitter_rand1000" : 4, "com_orkut_W": 4, "com_orkut_rand1000": 3, "webGraph_rand1000": 8, "friendster_rand1000": 1},
               "PPSP" : {"socLive_rand1000" : 20, "germany" : 35000, "road-usad_rand1000" : 4096, "road-usad_origweights" : 10000,"twitter_rand1000" : 4, "webGraph_rand1000": 8, "com_orkut_W": 4, "com_orkut_rand1000": 3, "friendster_rand1000": 1}, 
                  "Astar": {"germany" : 35000, "massachusetts" : 35000, "monaco" : 35000},
                  "wBFS": wBFS_runtime_param_dict},
    
    "galois" : {"deltastepping": {"friendster": 1, "com_orkut_W": 2, "com_orkut_rand1000": 2, "webGraph_rand1000": 2, "socLive_rand1000": 2, "road-usad_rand1000": 11, "twitter_rand1000": 0, "road-usad_origweights": 14, "friendster_rand1000": 0, "germany" : 15},
                "wBFS": {"socLive_rand1000": 0, "twitter_rand1000": 0, "com_orkut_W": 0, "webGraph_rand1000": 0, "friendster_rand1000": 0},
                "ppsp": {"com_orkut_W": 1, "com_orkut_rand1000": 2, "webGraph_rand1000": 1, "socLive_rand1000": 2, "road-usad_rand1000": 12, "road-usad_origweights": 13, "twitter_rand1000": 0, "friendster_rand1000": 0, "germany" : 15}, 
                "astar": {"germany" : 15, "massachusetts" : 14, "monaco" : 10, "road-u\
sad_origweights": 14}} # galois uses 2^d as its actual delta where d is the delta passed in using -delta arg
}


graphit_twitter_binary_dict = {"pr":"pagerank_pull_numa",
                                   "sssp" : "sssp_hybrid_denseforward",
                                   "cc" : "cc_hybrid_dense_bitvec_segment",
                                   "bfs" :"bfs_hybrid_dense_bitvec_segment",
                                   "prd" : "pagerankdelta_hybrid_dense_bitvec_numa",
                               "sssp_delta_stepping" : "sssp_delta_stepping_with_merge",
                               "sssp_delta_stepping_lazy" : "sssp_delta_stepping_lazy",
                               "ppsp_delta_stepping" : "ppsp_delta_stepping_with_merge"}

graphit_web_binary_dict = {"pr":"pagerank_pull_numa",
                                   "sssp" : "sssp_hybrid_denseforward",
                                   "cc" : "cc_hybrid_dense_bitvec_segment",
                                   "bfs" :"bfs_hybrid_dense_bitvec_segment",
                                   "prd" : "pagerankdelta_hybrid_dense_bitvec_numa",
                               "sssp_delta_stepping" : "sssp_delta_stepping_with_merge",
                               "sssp_delta_stepping_lazy" : "sssp_delta_stepping_lazy",
                               "ppsp_delta_stepping" : "ppsp_delta_stepping_with_merge"}


graphit_socLive_binary_dict = {"pr":"pagerank_pull", 
                                   "sssp" : "sssp_hybrid_denseforward",
                                   "cc" : "cc_hybrid_dense",
                                   "bfs" :"bfs_hybrid_dense",
                                   "prd" : "pagerankdelta_hybrid_dense",
                                   "sssp_delta_stepping" : "sssp_delta_stepping_no_merge",
                               "sssp_delta_stepping_lazy" : "sssp_delta_stepping_lazy",
                               "ppsp_delta_stepping" : "ppsp_delta_stepping_no_merge"
}

graphit_road_binary_dict = {"pr":"pagerank_pull",
                                     "sssp" : "sssp_push_slq",
                                     "cc" : "cc_hybrid_dense",
                                     "bfs" :"bfs_push_slq",
                                     "prd" : "pagerankdelta_hybrid_dense_split",
                            "sssp_delta_stepping" : "sssp_delta_stepping_with_merge",
                            "sssp_delta_stepping_lazy" : "sssp_delta_stepping_lazy",
                            "ppsp_delta_stepping" : "ppsp_delta_stepping_with_merge",
                            "astar" : "astar_with_merge"}

graphit_binary_map = {"socLive":graphit_socLive_binary_dict,
                      "socLive_rand1000" : graphit_socLive_binary_dict,
                      "socLive_logn" : graphit_socLive_binary_dict,
                      "twitter" : graphit_twitter_binary_dict,
                      "twitter_rand1000" : graphit_twitter_binary_dict,
                      "twitter_logn" : graphit_twitter_binary_dict,
                      "com_orkut_W" : graphit_socLive_binary_dict,
                      "com_orkut_rand1000" : graphit_socLive_binary_dict,
                      "webGraph" : {"pr":"pagerank_pull_numa",
                                    "sssp" : "sssp_hybrid_denseforward_segment",
                                    "cc" : "cc_hybrid_dense_bitvec_segment",
                                    "bfs" :"bfs_hybrid_dense_bitvec_segment",
                                    "prd" : "pagerankdelta_hybrid_dense_bitvec_numa"},
                      #webGraph uses the same binary as twitter graph
                      "webGraph_rand1000" : graphit_web_binary_dict,
                      "webGraph_logn" : graphit_web_binary_dict,
                      "friendster_rand1000" : graphit_twitter_binary_dict,
                      "friendster_logn" : graphit_twitter_binary_dict,
                      "friendster" : {"pr":"pagerank_pull_numa",
                                      "sssp" : "sssp_hybrid_denseforward_segment",
                                      "cc" : "cc_hybrid_dense_bitvec_segment",
                                      "bfs" :"bfs_hybrid_dense_bitvec_segment",
                                      "prd" : "pagerankdelta_hybrid_dense_bitvec_numa"},
                      "road-usad" : graphit_road_binary_dict,
                      "road-usad_rand1000" : graphit_road_binary_dict,
                      "road-usad_origweights" : graphit_road_binary_dict,
                      "netflix"   : {"cf" : "cf_pull_load_balance_segment"},
                      "netflix_2x"   : {"cf" : "cf_pull_load_balance_segment"},
                      "monaco" : graphit_road_binary_dict,
                      "germany" : graphit_road_binary_dict,
                      "massachusetts" : {"sssp" : "sssp_push_slq","astar" : "astar_with_merge"},
                      "road-central-usa_origweights": graphit_road_binary_dict
                      }

NUM_THREADS=48
PR_ITERATIONS=20

GreenMarl_PATH = "/data/scratch/baghdadi/green-marl/apps/output_cpp/bin/"
galois_PATH = "/data/scratch/yunming/galois/Galois-2.2.1/build/default/apps/"
galois_v4_PATH = "/data/scratch/xinyic/app_binaries/galois-v4/"
ligra_PATH = "/data/scratch/mengjiao/app_binaries/ligra/"
polymer_PATH = "/data/scratch/mengjiao/polymer/"
gemini_PATH = "/data/scratch/mengjiao/GeminiGraph/toolkits/"
gapbs_PATH = "/data/commit/graphit/yunming/app_binaries/gapbs/"
gapbs_prototype_PATH = "/data/commit/graphit/yunming/app_binaries/gapbs_prototype/"
julienne_PATH = "/data/commit/graphit/yunming/app_binaries/julienne/"
graphit_PATH = "/data/commit/graphit/yunming/app_binaries/graphit/"
grazelle_PATH = "/data/scratch/mengjiao/app_binaries/grazelle/"
DATA_PATH = "/data/commit/graphit/yunming/graphit_benchmark_graphs/"


def get_vertex_count(graph):
    graph_to_count = {"socLive": 4847571, "twitter": 61578415, "webGraph": 101717776,
                    "road-usad": 23947348, "friendster": 124836180, "nlpkkt240": 27993601}
    return graph_to_count[graph]
    
def path_setup(frameworks, LOG_DIR):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    for framework in frameworks:
        if not os.path.exists(LOG_DIR + framework):
            os.makedirs(LOG_DIR + framework);

def get_starting_points(graph):
    """ Use the points with non-zero out degree and don't hang during execution.  """
    if graph == "germany":
      return ["1087", "2019", "2019", "0", "3478", "134", "13", "47"]
    elif graph == "massachusetts":
      return ["0", "19", "101", "0", "1000", "44955", "3432", "23"]
    elif graph == "monaco":
      return ["0", "19", "101", "0", "234", "42", "1209", "47"]
    elif graph in ["com_orkut_W", "com_orkut_rand1000"]:
      return ["149", "149", "149", "34066", "34066", "34066", "2250603", "2250603", "2250603"]
    # elif graph == "webGraph_rand1000":
      # return ["5712", "57123", "234562", "789", "7890000", "326845", "1429214", "17926", "1321806"]
    elif graph not in ["friendster","friendster_rand1000", "friendster_logn"]:
        return ["14", "38", "47", "52", "53", "58", "59", "69", "94", "96"]
    else:
        # friendster takes a long time so use fewer starting points
        return ["101", "286", "16966", "37728", "56030", "155929"]


def get_ending_points(graph):
    if graph == "germany":
      return ["11111111", "1002019", "10002019", "12277374", "7832974", "4728972", "3478", "467823"]
    elif graph == "massachusetts":
      return ["121121", "448950", "111001", "448954", "40000", "48955", "298907", "4215"]
    elif graph == "monaco":
      return ["1111", "1589", "989", "1589", "807", "79", "1470", "48"]
    elif graph in ["com_orkut_W", "com_orkut_rand1000"]:
      return ["2250603", "52", "72789", "13", "2250603", "908977", "1971345", "1", "35"]
    # elif graph == "webGraph_rand1000":
      # return ["1429214", "1", "92798789", "1429214", "1", "43768907", "1430483", "1", "759469"]
    elif graph not in ["friendster", "friendster_rand1000"]:
        return ["69", "47", "52", "205",  "10005", "1000000",  "10005", "7000", "400000", "1000000"]
    else:
        # friendster takes a long time so use fewer ending points
        return ["286", "16966", "37728", "56030", "155929", "101"]

def get_cmd_grazelle(g, p):
    graph_path = DATA_PATH + g + "/" + g + "_grazelle.bin"
    command = grazelle_PATH + p
    if g in ["friendster", "friendster_rand1000", "friendster_logn"]:
        # run the binary built with 101 as starting point
        command += "101"
    command += " -i "  + graph_path + " -u 0,1"
    if p == "pr":
        command += " -N " + str(PR_ITERATIONS)
    return command

def get_cmd_greenmarl(g, p):
    graph_path = DATA_PATH + g + "/" + g + "_greenmarl.bin"
    args = graph_path + " " + str(NUM_THREADS) + " " + str(PR_ITERATIONS)
    command = GreenMarl_PATH + p + " " + args
    return "numactl -i all " + command

def get_cmd_ligra(g, p, point):
    # netflix graph is only used for collaborative filtering
    if (g == "netflix" and p != "CF"):
        return ""
    # social graphs are not to be used for cf
    if (g != "netflix" and p == "CF"):
        return ""

    args = ""
    if p in ["BellmanFord", "BFS", "BC"]:
        args += " -r " + point + " " 

    if g == "webGraph" or g == "friendster":
        if g == "friendster":
            # friendster is a symmetric graph
            args += " -s "

        # use binary format for large graphs
        args += " -b "
        if p == "BellmanFord" or p == "CF":
            graph_path = DATA_PATH + g + "/" + g + "-wgh_ligra_bin"
        else:
            graph_path = DATA_PATH + g + "/" + g + "_ligra_bin"
    else:
        if p == "BellmanFord" or p == "CF":
            graph_path = DATA_PATH + g + "/" + g + "_ligra.wadj"
        else:
            graph_path = DATA_PATH + g + "/" + g + "_ligra.adj"

    if p == "PageRank":
        args += " -maxiters 20 "
    elif p == "PageRankDelta":
        args += " -maxiters 10 "
    elif p == "CF":
        args += " -numiter 10 "

    if p == "BellmanFord" and g == "friendster":
        # need LONG option since there are 3.6*2=7.2 billion entries
        p += "_LONG"
                            
    args += graph_path
    command = ligra_PATH + p + " " + args 
    return "numactl -i all " + command

def get_cmd_polymer(g, p, point):
    if p == "numa-BellmanFord":
        graph_path = DATA_PATH + g + "/" + g + "_ligra.wadj"
    else:
        graph_path = DATA_PATH + g + "/" + g + "_ligra.adj"
    command = polymer_PATH + p + " " + graph_path
    if p == "numa-PageRank":
        command += " 20"
    if p == "numa-PageRankDelta":
        command += " 10"
    if p in ["numa-BellmanFord", "numa-BFS"]:
        command += " " + str(point)
    return command

def get_cmd_graphit(g, p, point, dst_point):
    # netflix graph is only used for collaborative filtering
    if (g in ["netflix", "netflix_2x"] and p != "cf"):
        return ""
    # social graphs are not to be used for cf
    if (g not in ["netflix", "netflix_2x"] and p == "cf"):
        return ""

    if (p in ["sssp", "sssp_delta_stepping", "sssp_delta_stepping_lazy", "ppsp_delta_stepping", "cf", "wBFS"]):
        graph_path = DATA_PATH + g + "/" + g + "_gapbs.wsg"
    elif p in ["astar"]:
        graph_path = DATA_PATH + g + "/" + g + ".bin"
    else:
        graph_path = DATA_PATH + g + "/" + g + "_gapbs.sg"

    args = graph_path
    if p in ["astar", "sssp","bfs","sssp_delta_stepping","sssp_delta_stepping_lazy","ppsp_delta_stepping", "wBFS"]:
        args += " " +  point

    if p in ["astar","ppsp_delta_stepping"]:
        args += " " +  dst_point

    # add runtime parameter
    if p in  ["sssp_delta_stepping", "sssp_delta_stepping_lazy", "ppsp_delta_stepping", "astar", "wBFS"] :
        args += " " + str(framework_app_graph_runtime_param_map["graphit"][p][g]) 

    #wBFS uses the same bianry as sssp_delta_stepping
    if p == "wBFS":
        p = "sssp_delta_stepping"
    command = graphit_PATH + graphit_binary_map[g][p] + " " + args

    if g in ["monaco",  "massachusetts"]:
        command = "taskset -c 0-11 " + command

    if g in ["twitter", "twitter_rand1000", "twitter_logn",  "webGraph", "friendster", "com_orkut_W", "com_orkut_rand1000", "webGraph_rand1000", "webGraph_logn", "friendster_rand1000", "friendster_logn", "socLive_rand1000", "socLive_logn", "road-central-usa_origweights", "road-usad_origweights", "germany"]:
        command = "numactl -i all " + command

        # flexible segment number
        if g == "friendster":
            command += " 30"
        else:
            command += " 16"
    return command

def get_cmd_gemini(g, p, point):
    graph_path = DATA_PATH + g + "/" + g + "_gemini.b"
    if (p == "sssp"):
        graph_path += "wel"
    else:
        graph_path += "el"
    args = graph_path + " " + str(get_vertex_count(g))
    if p in ["sssp", "bfs", "bc"]:
        args += " " + point
    elif (p == "pagerank"):
        args += " " + str(PR_ITERATIONS)
    command = gemini_PATH + p + " " + args
    return command

def get_cmd_galois(g, p, src_point, dst_point):
    if (p == "astar"):
        extension = "bin"
    elif p in ["sssp", "deltastepping", "ppsp", "wBFS"]:
        extension = "gr"
    else:
        extension = "vgr"
    
    if (g in ["com_orkut_W", "webGraph_rand1000"]):
        graph_path = DATA_PATH + g + "/" + g + "." + extension
    else:
        graph_path = DATA_PATH + g + "/" + g + "_galois." + extension
    
    if p == "astar":
        graph_path = DATA_PATH + g + "/" + g + "." + extension
    
    special_args = ""
    if p == "astar":
        special_args += " -algo=deltaStep" + " -startNode=" + src_point + " -reportNode=" + dst_point + " -delta=" + str(framework_app_graph_runtime_param_map["galois"][p][g]) + " "
    if p == "deltastepping" or p == "wBFS":
        special_args += " -algo=deltaStep" + " -startNode=" + src_point + " -delta=" + str(framework_app_graph_runtime_param_map["galois"][p][g]) + " "
    if p == "ppsp":
        special_args += " -algo=deltaStep" + " -startNode=" + src_point + " -reportNode=" + dst_point + " -delta=" + str(framework_app_graph_runtime_param_map["galois"][p][g]) + " "
    if p in ["bfs", "sssp", "betweennesscentrality"]:
        special_args += " -startNode=" + src_point + " "
    if p == "bfs" and g == "road-usad":
        special_args += " -algo=async "
    if p == "connectedcomponents":
        special_args += " -algo=labelProp " # use label propagation rather than union find to be fair
        transpose_graph = DATA_PATH + g + "/" + g + "_galois.tvgr" 
        special_args += " -graphTranspose=" + transpose_graph + " "
    if p == "sssp":
        special_args += " -algo=ligra " # use bellman-ford rather than delta stepping to be fair
        transpose_graph = DATA_PATH + g + "/" + g + "_galois.tgr" 
        special_args += " -graphTranspose=" + transpose_graph + " "
    if (p == "pagerank"):
        transpose_graph = DATA_PATH + g + "/" + g + "_galois.prpull" 
        special_args += " -maxIterations=" + str(PR_ITERATIONS) + " -graphTranspose=" + transpose_graph + " "
    
    args = graph_path + " -t=" + str(NUM_THREADS) + " " + special_args
    
    command = galois_PATH + p + "/" + p
    if p == "astar" or p == "ppsp" or p == "deltastepping":
        command = galois_v4_PATH + p
    if p == "wBFS":
        command = galois_v4_PATH + "deltastepping"
    if p == "betweennesscentrality":
        command += "-outer" # or "-inner"
    command += " " + args
    return "numactl -i all " + command

def get_cmd_julienne(g, p, src_point, dst_point):
    if (p in ["DeltaStepping", "PPSP", "wBFS"]):
        if (g in ["com_orkut_W", "webGraph_rand1000", "friendster_rand1000"]):
            graph_path = DATA_PATH + g + "/" + g + ".adj"
        else:
            graph_path = DATA_PATH + g + "/" + g + "_ligra.wadj"
    elif (p == "Astar"):
        graph_path = DATA_PATH + g + "/" + g + ".bin"
    else:
        graph_path = DATA_PATH + g + "/" + g + "_ligra.adj"
    args = ""
    if p in ["DeltaStepping", "PPSP", "Astar", "wBFS"]:
        args += " " +  " -src " + src_point

    #Laxman mentioned that we should use -s all the time 
    args += " -s " 

    if p in ["PPSP", "Astar"]:
        args += " -dst " + dst_point

    # add runtime parameter
    if p in ["DeltaStepping", "PPSP", "Astar", "wBFS"]:
        args += " -delta " + str(framework_app_graph_runtime_param_map["julienne"][p][g]) + " " 
       
    if p == "Astar":
        args += " -as "

    args += graph_path

    #wBFS uses the same binary as delta stepping, different runtime parameter
    if p == "wBFS":
        p = "DeltaStepping"

    command = julienne_PATH +  p + " " + args
    
    # adds numactl or taskset in the end for large social graphs 


    if g in ["road-usad", "road-usad_rand1000", "road-usad_origweights", "germany", "massachusetts", "monaco"]:
        command = "taskset -c 0-11 " + command
    else:
        command = "numactl -i all " + command
    return command

def get_cmd_gapbs(g, p, src_point, dst_point):
    if (p in ["delta_stepping", "ppsp", "delta_stepping_refactor", "wBFS"]):
        #if (g in ["com_orkut_W", "webGraph_rand1000"]):
        #    graph_path = DATA_PATH + g + "/" + g + ".wel"
        #else:
        graph_path = DATA_PATH + g + "/" + g + "_gapbs.wsg"
    elif (p == "astar"):
        graph_path = DATA_PATH + g + "/" + g + ".bin"
    else:
        graph_path = DATA_PATH + g + "/" + g + "_gapbs.sg"

    args = " -f " + graph_path

    if p in ["delta_stepping", "ppsp", "delta_stepping_refactor", "wBFS"]:
        args += " " +  " -r " + src_point
        
    if p == "ppsp":
        args += " -u " + dst_point
    
    if p == "astar":
        args += " -d " + str(framework_app_graph_runtime_param_map["gapbs"][p][g]) + " -b " + src_point + " -p " + dst_point

    #just run one trail 
    args += " -n 1"

    # add runtime parameter
    if p in  ["delta_stepping", "ppsp", "delta_stepping_refactor", "wBFS"] :
        args += " -d " + str(framework_app_graph_runtime_param_map["gapbs"][p][g]) 

    #wBFS and delta_stepping is using the same binary, just different runtime param (delta always 1)
    if p == "wBFS":
        p = "delta_stepping"
    command = gapbs_PATH +  p + " " + args
    
         
    if g in ["road-usad", "road-usad_rand1000", "road-usad_origweights", "germany", "massachusetts", "monaco"]:
        command = "taskset -c 0-11 " + command
    # adds numactl or taskset in the end for large social graphs 
    else:
        command = "numactl -i all " + command

    return command


def get_cmd_gapbs_prototype(g, p, src_point, dst_point):
    if (p in ["delta_stepping", "ppsp", "delta_stepping_refactor", "wBFS"]):
        graph_path = DATA_PATH + g + "/" + g + "_gapbs.wsg"
    else:
        graph_path = DATA_PATH + g + "/" + g + "_gapbs.sg"

    args = " -f " + graph_path

    if p in ["delta_stepping", "ppsp", "delta_stepping_refactor", "wBFS"]:
        args += " " +  " -r " + src_point
        
    if p == "ppsp":
        args += " -u " + dst_point
    
    #just run one trail 
    args += " -n 1"

    # add runtime parameter
    if p in  ["delta_stepping", "ppsp", "delta_stepping_refactor", "wBFS"] :
        args += " -d " + str(framework_app_graph_runtime_param_map["gapbs_prototype"][p][g]) 
        
    command = gapbs_prototype_PATH +  p + " " + args
    if p == "wBFS":
      command = gapbs_prototype_PATH + "delta_stepping"  + " " + args

    #command = "numactl -i all " + command
    #command = "taskset -c 0-11 " + command
     
    if p in ["ppsp"] and  g in ["road-usad", "road-usad_rand1000"]:
        command = "taskset -c 0-11 " + command
    # adds numactl or taskset in the end for large social graphs 
    else:
        command = "numactl -i all " + command


    return command

#potentially providing both a source and destination point to each framework

def get_cmd(framework, graph, app, src_point, dst_point = 0):
    if framework == "greenmarl":
        cmd = get_cmd_greenmarl(graph, app)
    elif framework == "ligra":
        cmd = get_cmd_ligra(graph, app, src_point)
    elif framework == "galois":
        cmd = get_cmd_galois(graph, app,  src_point, dst_point)
    elif framework == "graphit":
        cmd = get_cmd_graphit(graph, app,  src_point, dst_point)
    elif framework == "grazelle":
        cmd = get_cmd_grazelle(graph, app)
    elif framework == "polymer":
        cmd = get_cmd_polymer(graph, app,  src_point)
    elif framework == "gapbs":
        cmd = get_cmd_gapbs(graph,app,  src_point, dst_point)
    elif framework == "gapbs_prototype":
        cmd = get_cmd_gapbs_prototype(graph,app,  src_point, dst_point)
    elif framework == "julienne":
        cmd = get_cmd_julienne(graph, app, src_point, dst_point)
    elif framework == "gemini":
        cmd = get_cmd_gemini(graph, app, point)
    else:
        print("unsupported framework: " + framework)
    return cmd

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--frameworks', nargs='+',
                        default=[], # "netflix" only used for cf
                        help="frameworks to benchmark: " + ' '.join(["galois", "ligra", "graphit", "greenmarl", "gemini", "gapbs", "julienne"]))


    # graphs include "socLive", "road-usad", "twitter", "webGraph", "friendster", "socLive_rand1000", "twitter_rand1000", "road_rand1000", "germany", "massachusetts", "monaco" . (the unweighted version of rand1000 graphs are the same as the original ones, just symlinks)
    parser.add_argument('-g', '--graphs', nargs='+',
                        default=["socLive"],
                        help="graphs to run the applications on. Defaults to all five graphs.")
    # applications include bfs, sssp, pr, cc, cf, ds, astar (delta stepping)
    parser.add_argument('-a', '--applications', nargs='+',
                        default=[], # "prd" and "cf" only exists in ligra and graphit
                        help="applications to benchmark. Choices are bfs, sssp, pr, cc, cf, ds, ppsp, astar.")

    parser.add_argument('-p', '--logPath', default="./benchmark_logs/", help="path to the log directory")


    args = parser.parse_args()
    LOG_DIR = args.logPath + "/"

    path_setup(args.frameworks, LOG_DIR)

    for graph in args.graphs:
        for framework in args.frameworks:
            for generic_app_name in args.applications:
                assert generic_app_name in framework_app_lookup[framework]
                
                app = framework_app_lookup[framework][generic_app_name]
                log_file_str = LOG_DIR + framework + "/" + generic_app_name + "_" + graph + ".txt"
                log_file = open(log_file_str, "w+")
                successes = 0
                starting_points = get_starting_points(graph)
                ending_points = get_ending_points(graph)
                for i in range(len(starting_points)):
                    starting_point = starting_points[i]
                    ending_point = ending_points[i]
                    cmd = get_cmd(framework, graph, app, starting_point, ending_point)
                    if not cmd:
                        break
                    print cmd

                    # setup timeout for executions that hang
                    kill = lambda process: process.kill()
                    out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    timer = Timer(600, kill, [out]) # timeout after 10 min
                    try:
                        timer.start()
                        (output, err) = out.communicate()
                    finally:
                        timer.cancel()

                    if output:
                        successes += 1
                        log_file.write("\n------------------------------------------------\n")
                        log_file.write(time.strftime("%d/%m/%Y-%H:%M:%S"))
                        log_file.write("\n")
                        log_file.write(output)
                        log_file.write("\n------------------------------------------------\n")
                        if generic_app_name in ["pr", "cc", "prd", "cf"] or framework in ["greenmarl", "grazelle"]:
                            # pagerank, cc, prd, and cf can return when they succeeds once.
                            # greenmarl sets starting point internally
                            break;            
                log_file.write("successes=" + str(successes) + "\n")
                log_file.close()


if __name__ == "__main__":
    main()
