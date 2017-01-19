#!/usr/bin/env python
#
# Copyright (c) 2016 Cisco and/or its affiliates.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from string import Template

import util

proto_template = Template("""
package $plugin_package.$proto_package;

/**
 * <p>This class represents $description.
 * <br>It was generated by proto_gen.py based on $inputfile preparsed data:
 */

syntax = "proto3";

option java_multiple_files=true;
option java_package = $plugin_package.$proto_package;

service $cls_name {
$rpcs
}

$messages
""")

message_template = Template('''  message $msgname$suffix {\n$fields\n  }\n''')

field_template = Template("""    $type $name = $id;\n""")

rpc_template = Template("""  rpc $func (${func}Message) returns (${func}MessageReply)\n""")


def generate_protos(func_list, base_package, plugin_package, plugin_name, proto_package, inputfile):
    """ Generates proto objects in a dedicated package """
    print "Generating PROTOs"
    rpcs = ""
    messages = ""
    description = "proto file"
    camel_case_plugin_name = util.underscore_to_camelcase_upper(plugin_name)
    if not os.path.exists(proto_package):
        os.mkdir(proto_package)

    proto_path = os.path.join(proto_package, camel_case_plugin_name + ".proto")
    print "PROTOs path: "+proto_path
    for func in func_list:
        camel_case_proto_name = util.underscore_to_camelcase_upper(func['name'])
        camel_case_method_name = util.underscore_to_camelcase(func['name'])
        print "processing "+ camel_case_method_name

        if util.is_ignored(func['name']) or util.is_control_ping(camel_case_proto_name):
            continue

        messages += generate_proto_messages(camel_case_proto_name, func)

        # Generate request/reply or dump/dumpReply even if structure can be used as notification
        if not util.is_just_notification(func["name"]):
            if not util.is_reply(camel_case_proto_name):
#                description = "reply DTO"
#                request_proto_name = get_request_name(camel_case_dto_name, func['name'])
#                if util.is_details(camel_case_dto_name):
                    # FIXME assumption that dump calls end with "Dump" suffix. Not enforced in vpe.api
#                    base_type += "JVppReply<%s.%s.%s>" % (plugin_package, dto_package, request_dto_name + "Dump")
#                    generate_dump_reply_dto(request_dto_name, base_package, plugin_package, dto_package,
#                                            camel_case_dto_name, camel_case_method_name, func)
#                else:
#                    base_type += "JVppReply<%s.%s.%s>" % (plugin_package, dto_package, request_dto_name)
                 rpcs += rpc_template.substitute(func=camel_case_proto_name)

        # for structures that are also used as notifications, generate dedicated notification DTO
#       if util.is_notification(func["name"]):
#           base_type = "JVppNotification"
#           description = "notification DTO"
#           camel_case_dto_name = util.add_notification_suffix(camel_case_dto_name)
#           dto_path = os.path.join(dto_package, camel_case_dto_name + ".java")
#           methods = generate_dto_base_methods(camel_case_dto_name, func)
#           write_dto_file(base_package, plugin_package, base_type, camel_case_dto_name, description, dto_package,
#                          dto_path, fields, func, inputfile, methods)
    write_proto_file(base_package, plugin_package, camel_case_proto_name, description, proto_package,
                   proto_path, rpcs, func, inputfile, messages)

    #flush_dump_reply_protos(inputfile)

def generate_proto_messages(camel_case_proto_name, func):
    fields = ""
    messages = ""
    end = "Message"
    i=1;
    for t in zip(func['types'], func['args']):
        # for retval don't generate dto field in Reply
        type_prefix = ""
        field_name = util.underscore_to_camelcase(t[1])
        if util.is_reply(camel_case_proto_name):
            if util.is_details(camel_case_proto_name):
                type_prefix="stream "
            else:
                end="MessageReply"
        fields += field_template.substitute(type=type_prefix+util.jni_2_proto_type_mapping[t[0]],
                                            name=field_name,
                                            id=i)
        i+=1
    messages += message_template.substitute(msgname=camel_case_proto_name,
                                                fields=fields,
                                                suffix=end)
    print messages
    return messages

def write_proto_file(base_package, plugin_package, camel_case_proto_name, description, proto_package, proto_path,
                   rpcs, func, inputfile, messages):
    proto_file = open(proto_path, 'w')
    print "writing proto file"
    proto_file.write(proto_template.substitute(inputfile=inputfile,
                                           description=description,
                                           cls_name=camel_case_proto_name,
                                           rpcs=rpcs,
                                           messages=messages,
                                           base_package=base_package,
                                           plugin_package=plugin_package,
                                           proto_package=proto_package))
    proto_file.flush()
    proto_file.close()


# Returns request name or special one from unconventional_naming_rep_req map
def get_request_name(camel_case_dto_name, func_name):
    return util.underscore_to_camelcase_upper(
        util.unconventional_naming_rep_req[func_name]) if func_name in util.unconventional_naming_rep_req \
        else util.remove_reply_suffix(camel_case_dto_name)
