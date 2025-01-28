import argparse
from environment import KubernetesEnv


def main():
    parser = argparse.ArgumentParser(
        description="Manage the Kubernetes environment")
    parser.add_argument("action", help="The action to perform",
                        choices=["reset", "delete", "prepare"])
    args = parser.parse_args()

    environment = KubernetesEnv()
    match args.action:
        case "reset":
            environment.reset()
        case "delete":
            environment.delete()
        case "prepare":
            environment.prepare()


if __name__ == "__main__":
    main()
