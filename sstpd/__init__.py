#!/usr/bin/env python2
import sys
import logging
import argparse
from twisted.internet.endpoints import SSL4ServerEndpoint
from twisted.internet import reactor, ssl

from protocols import SSTPProtocolFactory
from address import IPPool


def _getArgs():
    parser = argparse.ArgumentParser(description='A Secure Socket Tunneling '
            'Protocol (SSTP) server.',
            epilog='Auther: Sorz <orz@sorz.org>.')
    parser.add_argument('-l', '--listen',
            default='',
            metavar='ADDRESS',
            help='The address to bind to, default to all.')
    parser.add_argument('-p', '--listen-port',
            default=443, type=int,
            metavar='PORT')
    parser.add_argument('-c', '--pem-cert',
            metavar='PEM-FILE',
            help='The path of PEM-format certificate with key.')
    parser.add_argument('-n', '--no-ssl',
            action='store_true',
            help='Use plain HTTP instead of HTTPS. '
                 'Useful when running behind a reverse proxy.')
    parser.add_argument('--pppd',
            default='/usr/sbin/pppd',
            metavar='PPPD-FILE')
    parser.add_argument('--pppd-config',
            default='/etc/ppp/options.sstpd',
            metavar='CONFIG-FILE',
            help='Default to /etc/ppp/options.sstpd')
    parser.add_argument('--local',
            default='192.168.20.1',
            metavar='ADDRESS',
            help="Address of server side on ppp, default to 192.168.20.1")
    parser.add_argument('--remote',
            default='192.168.20.0/24',
            metavar='NETWORK',
            help="Address of client will be selected from it, "
                "default to 192.168.20.0/24")

    return parser.parse_args()


def _load_cert(path):
    if not path:
        logging.error('argument -c/--pem-cert is required')
        return
    try:
        certData = open(path).read()
    except IOError as e:
        logging.critical(e)
        logging.critical('Cannot read certificate.')
        return
    return ssl.PrivateCertificate.loadPEM(certData)


def main():
    logging.basicConfig(level=logging.INFO,
            format='%(asctime)s %(levelname)-s: %(message)s')
    args = _getArgs()

    ippool = IPPool(args.remote)
    ippool.register(args.local)

    factory = SSTPProtocolFactory(pppd=args.pppd, pppdConfigFile=args.pppd_config,
            local=args.local, remotePool=ippool)

    if args.no_ssl:
        logging.info('Running without SSL.')
        reactor.listenTCP(args.listen_port, factory)
    else:
        certificate = _load_cert(args.pem_cert)
        if certificate is None:
            logging.critical('Cannot read certificate.')
            sys.exit(2)
            return
        reactor.listenSSL(args.listen_port, factory,
                certificate.options(), interface=args.listen)

    logging.info('Listening on %s:%s...' % (args.listen, args.listen_port))
    reactor.run()


if __name__ == '__main__':
    main()
