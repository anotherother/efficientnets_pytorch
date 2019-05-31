import os
import argparse
import torch
import torch.nn as nn

from neural_net.effnet import EfficientNet
from runner import Runner
from dataloaders.loader import get_loaders

from utils.logger import Logger


def arg_parse():
    parser = argparse.ArgumentParser(description='EfficientNet')
    parser.add_argument('--save_dir', type=str, required=True,
                        help='Directory name to save the model')

    parser.add_argument('--root', type=str, default="/data2/imagenet",
                        help="The Directory of data path.")
    parser.add_argument('--gpus', type=str, default="0,1,2,3",
                        help="Select GPU Numbers | 0,1,2,3 | ")
    parser.add_argument('--num_workers', type=int, default="32",
                        help="Select CPU Number workers")

    parser.add_argument('--model', type=str, default='b0',
                        choices=["b0"],
                        help='The type of Efficient net.')

    parser.add_argument('--epoch', type=int, default=350, help='The number of epochs')
    parser.add_argument('--batch_size', type=int, default=1024, help='The size of batch')
    parser.add_argument('--test', action="store_true", help='Only Test')
    parser.add_argument('--dropout_rate', type=float, default=0.2)
    parser.add_argument('--dropconnect_rate', type=float, default=0.2)
    parser.add_argument('--optim', type=str, default='rmsprop', choices=["rmsprop"])
    parser.add_argument('--lr',    type=float, default=0.016, help="Base learning rate when train batch size is 256.")

    # Adam Optimizer
    parser.add_argument('--beta', nargs="*", type=float, default=(0.5, 0.999))
    parser.add_argument('--momentum', type=float, default=0.9)
    parser.add_argument('--eps',      type=float, default=0.001)
    parser.add_argument('--decay',    type=float, default=1e-5)
    return parser.parse_args()


def get_model(arg, classes=1000):
    if arg.model == "b0":
        return EfficientNet(1, 1, num_classes=classes)


if __name__ == "__main__":
    arg = arg_parse()

    arg.save_dir = "%s/outs/%s" % (os.getcwd(), arg.save_dir)
    if os.path.exists(arg.save_dir) is False:
        os.mkdir(arg.save_dir)

    logger = Logger(arg.save_dir)
    logger.will_write(str(arg) + "\n")

    os.environ["CUDA_VISIBLE_DEVICES"] = arg.gpus
    torch_device = torch.device("cuda")

    train_loader, val_loader = get_loaders(arg.root, arg.batch_size, 224, arg.num_workers)

    net = get_model(arg, classes=1000)
    net = nn.DataParallel(net).to(torch_device)
    loss = nn.CrossEntropyLoss()

    optim = {
        # "adam" : lambda : torch.optim.Adam(net.parameters(), lr=arg.lr, betas=arg.beta, weight_decay=arg.decay),
        "rmsprop" : lambda : torch.optim.RMSprop(net.parameters(), lr=arg.lr, momentum=arg.momentum, eps=arg.eps, weight_decay=arg.decay)
    }[arg.optim]()

    model = Runner(arg, net, optim, torch_device, loss, logger)
    if arg.test is False:
        model.train(train_loader, val_loader)
    model.test(train_loader, val_loader)
