#!/usr/bin/env ruby
require "fileutils"
require "json"
require "optparse"
require "uri"

options = {}
OptionParser.new do |parser|
  parser.on("--sing-box PATH") { |value| options[:sing_box] = value }
  parser.on("--output DIR") { |value| options[:output] = value }
end.parse!

abort "Set PROXY_URI" if ENV["PROXY_URI"].to_s.strip.empty?
abort "Pass --sing-box PATH" unless options[:sing_box]
abort "Pass --output DIR" unless options[:output]

uri_text = ENV.fetch("PROXY_URI").strip
uri = URI(uri_text)
abort "PROXY_URI must use vless://" unless uri.scheme == "vless"
query = URI.decode_www_form(uri.query.to_s).to_h
uuid = URI.decode_www_form_component(uri.user.to_s)
name = URI.decode_www_form_component(uri.fragment.to_s)
name = "private-vless-reality" if name.empty?

required = %w[security sni pbk sid flow]
missing = required.reject { |key| query[key] && !query[key].empty? }
abort "Missing URI fields: #{missing.join(', ')}" unless missing.empty?

FileUtils.mkdir_p(options[:output], mode: 0o700)

files = {
  "vless-uri.txt" => uri_text + "\n",
  "manual-parameters.txt" => <<~TEXT,
    Name: #{name}
    Protocol: VLESS
    Server: #{uri.host}
    Port: #{uri.port}
    UUID: #{uuid}
    Encryption: #{query.fetch("encryption", "none")}
    Flow: #{query["flow"]}
    Transport: #{query.fetch("type", "tcp")}
    Security: #{query["security"]}
    SNI / Server Name: #{query["sni"]}
    Reality Public Key: #{query["pbk"]}
    Reality Short ID: #{query["sid"]}
    Client Fingerprint: #{query.fetch("fp", "chrome")}
  TEXT
  "clash-meta.yaml" => <<~YAML
    proxies:
      - name: #{name.inspect}
        type: vless
        server: #{uri.host}
        port: #{uri.port}
        uuid: #{uuid.inspect}
        network: #{query.fetch("type", "tcp")}
        tls: true
        udp: true
        flow: #{query["flow"]}
        servername: #{query["sni"]}
        client-fingerprint: #{query.fetch("fp", "chrome")}
        reality-opts:
          public-key: #{query["pbk"]}
          short-id: #{query["sid"]}
  YAML
}

files.each do |filename, content|
  path = File.join(options[:output], filename)
  abort "Refusing to overwrite #{path}" if File.exist?(path)
  File.open(path, File::WRONLY | File::CREAT | File::EXCL, 0o600) { |file| file.write(content) }
end

config = JSON.parse(File.read(options[:sing_box]))
target = File.join(options[:output], "sing-box.json")
abort "Refusing to overwrite #{target}" if File.exist?(target)
File.open(target, File::WRONLY | File::CREAT | File::EXCL, 0o600) do |file|
  file.write(JSON.pretty_generate(config))
  file.write("\n")
end

puts "Created four protected client files in #{options[:output]}"
