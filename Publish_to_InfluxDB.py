import json
import requests
import sseclient
import time as time
import decoder as de
from termcolor import colored
from influxdb import InfluxDBClient


# Credentials are store in a GIT IGNORE'ed file
import credentials as cd


# particles to watch
good_particles = [
    '450035000a51353335323536'
]

# make sure this is current
access_token = cd.access_token

# influx credentials
usr = cd.usr
password = cd.passwd
db = cd.db
host = cd.host
port = cd.port
measurement = cd.measurement
client = InfluxDBClient(host, port, usr, password, db)

# will hold all registered particles
particles = {}

# this is a list of messages that need to be understood and programmed for
unknown_messages = [
    'spark/device/app-hash',
    'spark/device/last_reset'
]


class Particle:
    def __init__(self, _id, name, last_app, last_ip_address, last_heard, product_id, connected, platform_id,
                 cellular, status):

        # Particle defined attributes
        self.id = _id
        self.name = name
        self.last_app = last_app
        self.last_ip_address = last_ip_address
        self.last_heard = last_heard
        self.product_id = product_id
        self.connected = connected
        self.platform_id = platform_id
        self.cellular = cellular
        self.status = status

        # Particles APIs
        self.api = "https://api.particle.io/v1/devices/" + self.id + "/?access_token=" + access_token
        self.var_api = 'https://api.particle.io/v1/devices/' + self.id + '/?access_token=' + access_token
        self.result_api = ''

        # Chaos defined attributes
        self.has_location = False
        self.location = "unknown"
        self.experiment = "unknown"
        self.var_req = None
        self.var_json = None
        self.variables = []
        self.current_var = None
        self.measurements = {}

        # Gather more data if device is connected
        if self.connected:
            try:
                self.get_variables()
            except:
                self.connected = False
                print self.name + ' is now offline.'

    def print_attributes(self):
        print '\n' + colored(self.name, 'red')
        print 'Location: ',
        try:
            print colored(self.location, 'green')
        except:
            print colored('Unknown', 'green')
        print 'Connected: ' + colored(self.connected, 'blue')
        print 'Variables are:'
        for i in self.variables:
            print i

    def generate_result_url(self):
        self.result_api = 'https://api.particle.io/v1/devices/' + self.id + '/' + self.current_var + '/?access_token=' + access_token
        return self.result_api

    def get_variables(self):
        # reset our variable list
        self.variables = []

        try:
            self.var_req = requests.get(self.var_api)
            self.var_json = self.var_req.json()['variables']
            try:
                self.variables = [v for v in self.var_json]
            except TypeError:
                self.connected = False
                print self.name + ' status was updated: Connected = ',
                print colored(self.connected, 'blue')

            # # add measurements for each variable
            # for v in self.variables:
            #     self.measurements[v] = m.return_measurement(v)

            if 'location' in self.variables:
                self.has_location = True
                self.location = 'known'
                self.variables = [v for v in self.variables if v != 'location']
                print '\n' + colored(self.name, 'red')
                print 'finding location...'
                try:
                    self.current_var = 'location'
                    self.generate_result_url()
                    self.var_req = requests.get(self.result_api)
                    self.var_json = self.var_req.json()
                    self.location = self.var_json['result']
                    print 'Device\'s location is: ',
                    print colored(self.location, 'green')
                except:
                    print 'Error retrieving location'

            print 'It\'s ' + colored('variables', 'green') + ' are: '
            for v in self.variables:
                print v
                # print self.measurements[v]
        except KeyError:
            print 'This particles has no variables'


# deviceAPI
class DeviceAPI:
    def __init__(self):
        self.url = 'https://api.particle.io/v1/devices/?access_token=' + access_token

        self.devices_req = None
        self.devices_json = None
        self.claimed = 0
        self.connected = 0
        self.selected_particle = None

        self.start_time = 0
        self.end_time = 0
        self.duration = 0

        # create particle objects, and time it
        print colored('\nWELCOME', 'cyan')
        print 'Creating Particle objects...'
        self.start_time = time.time()
        self.create_particles()  # this is where the magic happens
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        print '\nIt took ' + colored(self.duration, 'red') + ' seconds.'

    def get_particles(self):
        self.devices_req = requests.get(self.url)
        self.devices_json = self.devices_req.json()
        return self.devices_json

    # generates a dictionary of particles from the Particles DeviceAPI
    def create_particles(self):
        for l in self.get_particles():
            if l['id'] in good_particles:
                particles[l['id']] = Particle(
                    l['id'],
                    l['name'],
                    l['last_app'],
                    l['last_ip_address'],
                    l['last_heard'],
                    l['product_id'],
                    l['connected'],
                    l['platform_id'],
                    l['cellular'],
                    l['status'],
                )


    # updates all the claimed particles with the results of Particles DeviceAPI call
    def update_particles(self):
        for l in self.get_particles():
            if l['id'] in good_particles:
                particles[l['id']].id = l['id']
                particles[l['id']].name = l['name']
                particles[l['id']].id = l['id']
                particles[l['id']].name = l['name']
                particles[l['id']].last_app = l['last_app']
                particles[l['id']].last_ip_address = l['last_ip_address']
                particles[l['id']].last_heard = l['last_heard']
                particles[l['id']].product_id = l['product_id']
                particles[l['id']].connected = l['connected']
                particles[l['id']].platform_id = l['platform_id']
                particles[l['id']].cellular = l['cellular']  # that really doesn't need to be there
                particles[l['id']].status = l['status']

    def connected_particles(self):
        if particles:
            self.update_particles()  # update the device statuses
            self.enumerate_connected()
        else:
            self.create_particles()
            self.connected_particles()

    def enumerate_connected(self):
        self.connected = 0
        for p in particles:
            if particles[p].connected:
                self.connected += 1
        print '\nThere are ' + str(self.connected) + colored(' connected', 'green') + ' Particles:'
        for p in particles:
            if particles[p].connected:
                self.selected_particle = particles[p]
                print self.selected_particle.name,
                # print 'Location:',
                # print particles[p].location,
                print particles[p].id,
                print particles[p].name


class SSEClient:
    def __init__(self):
        self.url = 'https://api.particle.io/v1/devices/events?access_token=' + access_token
        self.client = None
        self.event = None
        self.data = None
        self.json_body = None
        self.measurement = None
        self.particle_to_update = ''
        self.json2write = None

    def start_sse(self):
        self.client = sseclient.SSEClient(self.url)
        for event in self.client:
            if type(event.data) is not str:
                # set object attributes to current event
                self.event = event.event
                self.data = event.data
                self.data = json.loads(self.data)

                if self.data['coreid'] in good_particles:
                    # if the event is a status change, update
                    if self.event == 'spark/status':
                        self.particle_to_update = self.data['coreid']
                        if self.data['data'] == 'online':
                            particles[self.particle_to_update].connected = True
                            particles[self.particle_to_update].get_variables()
                        elif self.data['data'] == 'offline':
                            particles[self.particle_to_update].connected = False
                        else:
                            print colored('Unknown spark status', 'yellow')

                        print particles[self.particle_to_update].name + ' status was updated: Connected = ',
                        print colored(particles[self.particle_to_update].connected, 'blue')

                        # add a call to update particle if connected = True
                        self.particle_to_update = None

                    elif self.event == 'spark/device/app-hash':
                        print colored('HOLY SHIT', 'red'),
                        print 'we got a ',
                        print colored('spark/device/app-hash', 'green'),
                        print 'event. Better figure out what to do with those!'
                    # otherwise

                    else:
                        # generate the influx object, by passing the appropriate particle
                        self.influx_write(
                            self.data['coreid'],
                            self.event,
                            self.data['published_at'],
                            self.data['data']
                        )

        def json_write(self, measurement, name, location, _time, _type, value, specific=None):
            self.json2write = [
                {
                "measurement": measurement,
                "tags": {
                    'name': name,
                    'location': location,
                    'label': specific,
                },
                "time": _time,
                "fields": {
                    _type: value,
                }
            }
        ]
        return self.json2write

    def influx_write(self, _id, key, _time, value):
        if particles:
            # When new code is flashed
            # print event
            # print value

            # Start working
            if key == 'spark/flash/status':
                if value == 'started':
                    print colored(particles[_id].name, 'red') + 'is being ' + colored('flashed', 'red')
                elif value == 'success':
                    print colored(particles[_id].name, 'red') + 'flash ' + colored('successful!', 'green')
                self.json_body = [
                    {
                        "measurement": 'firmware',
                        "tags": {
                            "name": particles[_id].name,
                            'location': particles[_id].location
                        },
                        "time": _time,
                        "fields": {
                            "value": value,
                        }
                    }
                ]
                client.write_points(self.json_body)
                return
            #
            # try:
            #     particles[_id].name
            # except:
            #     print colored("NEW ", 'green'),
            #     print "Particle has been added, ",
            #     print colored("creating object "),
            #     print "for Particle",
            #     print colored(_id, "blue")

            # return the TYPE of event (basically units)
            # if it doesn't exist, add it to the object
            # try:
            #     print particles[_id].measurements[event.lower()],
            # except KeyError:
            #     particles[_id].measurements[event] = m.return_measurement(event.lower())
            #     print particles[_id].measurements[event],
            # print event,
            # print value,
            # print particles[_id].name,
            # print _time,
            # client.write_points(self.json_body)
            # print colored('SENT', 'green')

            # KEY:
            # r[0] = label
            # r[1] = value
            # r[2] = event
            # r[3] = unit
            for r in de.decode_event(key, value):
                # print r[0], r[1], r[2], r[3]
                self.json_body = [
                    {
                        "measurement": measurement,
                        "tags": {
                            "experiment": 'unknown',
                            'location': particles[_id].location,
                            "label": r[0],
                            "event": r[2],
                            "unit": r[3],
                            "name": particles[_id].name,
                        },
                        "time": _time,
                        "fields": {
                            "value": r[1],
                        }
                    }
                ]
                print self.json_body
                client.write_points(self.json_body)

        else:
            print 'Particles have not been created!'


d = DeviceAPI()
d.connected_particles()

s = SSEClient()
print '\nStarting SSE Client...'
while True:
    # try:
    s.start_sse()
    # except:
    #     print colored("FATAL ERROR, restarting", 'red')


