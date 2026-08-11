#!/usr/bin/env ruby
require "digest"
require "fileutils"
require "ipaddr"
require "json"
require "optparse"
require "time"

PRIVATE_CIDRS = %w[
  0.0.0.0/8
  10.0.0.0/8
  100.64.0.0/10
  127.0.0.0/8
  169.254.0.0/16
  172.16.0.0/12
  192.0.0.0/24
  192.0.2.0/24
  192.168.0.0/16
  198.18.0.0/15
  198.51.100.0/24
  203.0.113.0/24
  224.0.0.0/4
  240.0.0.0/4
  ::1/128
  fc00::/7
  fe80::/10
  ff00::/8
].freeze

options = {
  sing_direct_tag: "direct",
  sing_proxy_tag: "proxy",
  mihomo_direct_tag: "DIRECT",
  mihomo_proxy_tag: "PROXY"
}

OptionParser.new do |parser|
  parser.on("--policy PATH") { |value| options[:policy] = value }
  parser.on("--output DIR") { |value| options[:output] = value }
  parser.on("--proxy-server HOST") { |value| options[:proxy_server] = value }
  parser.on("--sing-direct-tag TAG") { |value| options[:sing_direct_tag] = value }
  parser.on("--sing-proxy-tag TAG") { |value| options[:sing_proxy_tag] = value }
  parser.on("--mihomo-direct-tag TAG") { |value| options[:mihomo_direct_tag] = value }
  parser.on("--mihomo-proxy-tag TAG") { |value| options[:mihomo_proxy_tag] = value }
end.parse!

abort "Pass --policy PATH" unless options[:policy]
abort "Pass --output DIR" unless options[:output]
abort "Pass --proxy-server HOST" unless options[:proxy_server]

def normalize_domain(value)
  domain = value.to_s.strip.downcase.sub(/\A\./, "")
  abort "Invalid domain: #{value.inspect}" if domain.empty? || domain.include?("://") || domain.include?("/")
  labels = domain.split(".")
  valid = labels.all? { |label| label.match?(/\A[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\z/) }
  abort "Invalid domain: #{value.inspect}" unless valid && domain.length <= 253
  domain
end

def normalize_cidr(value)
  cidr = value.to_s.strip
  IPAddr.new(cidr)
  abort "CIDR prefix required: #{value.inspect}" unless cidr.include?("/")
  cidr
rescue IPAddr::InvalidAddressError
  abort "Invalid CIDR: #{value.inspect}"
end

def normalize_list(values, &block)
  Array(values).map(&block).uniq.sort
end

def yaml_quote(value)
  JSON.generate(value.to_s)
end

def write_protected(path, content)
  abort "Refusing to overwrite #{path}" if File.exist?(path)
  File.open(path, File::WRONLY | File::CREAT | File::EXCL, 0o600) { |file| file.write(content) }
end

policy = JSON.parse(File.read(options[:policy]))
abort "Unsupported routing policy schema" unless policy["schema_version"] == 1

upstreams = policy.fetch("upstreams")
custom = policy.fetch("custom")
direct_domains = normalize_list(custom["direct_domains"]) { |value| normalize_domain(value) }
proxy_domains = normalize_list(custom["proxy_domains"]) { |value| normalize_domain(value) }
block_domains = normalize_list(custom["block_domains"]) { |value| normalize_domain(value) }
direct_cidrs = normalize_list(custom["direct_ip_cidrs"]) { |value| normalize_cidr(value) }
proxy_cidrs = normalize_list(custom["proxy_ip_cidrs"]) { |value| normalize_cidr(value) }

domain_groups = {
  "direct_domains" => direct_domains,
  "proxy_domains" => proxy_domains,
  "block_domains" => block_domains
}
domain_groups.keys.combination(2) do |left, right|
  conflicts = domain_groups[left] & domain_groups[right]
  abort "Domain conflicts between #{left} and #{right}: #{conflicts.join(', ')}" unless conflicts.empty?
end

cidr_conflicts = direct_cidrs & proxy_cidrs
abort "CIDR conflicts between direct and proxy: #{cidr_conflicts.join(', ')}" unless cidr_conflicts.empty?

proxy_server = options[:proxy_server].to_s.strip
abort "Empty proxy server" if proxy_server.empty?
begin
  proxy_server_address = IPAddr.new(proxy_server)
  proxy_server_ip = true
rescue IPAddr::InvalidAddressError
  proxy_server = normalize_domain(proxy_server)
  proxy_server_ip = false
end
proxy_server_cidr = if proxy_server_ip
  "#{proxy_server}/#{proxy_server_address.ipv4? ? 32 : 128}"
end

sing_direct = options[:sing_direct_tag]
sing_proxy = options[:sing_proxy_tag]
sing_rules = [
  { "action" => "sniff" },
  { "protocol" => "dns", "action" => "hijack-dns" }
]
server_match = proxy_server_ip ? { "ip_cidr" => [proxy_server_cidr] } : { "domain" => [proxy_server] }
sing_rules << server_match.merge("action" => "route", "outbound" => sing_direct)
sing_rules << { "ip_cidr" => PRIVATE_CIDRS, "action" => "route", "outbound" => sing_direct }
sing_rules << { "domain_suffix" => block_domains, "action" => "reject" } unless block_domains.empty?
sing_rules << { "domain_suffix" => proxy_domains, "action" => "route", "outbound" => sing_proxy } unless proxy_domains.empty?
sing_rules << { "domain_suffix" => direct_domains, "action" => "route", "outbound" => sing_direct } unless direct_domains.empty?
sing_rules << { "ip_cidr" => proxy_cidrs, "action" => "route", "outbound" => sing_proxy } unless proxy_cidrs.empty?
sing_rules << { "ip_cidr" => direct_cidrs, "action" => "route", "outbound" => sing_direct } unless direct_cidrs.empty?
sing_rules << { "rule_set" => "geosite-cn", "action" => "route", "outbound" => sing_direct }
sing_rules << { "rule_set" => "geoip-cn", "action" => "route", "outbound" => sing_direct }

sing_box = {
  "route" => {
    "auto_detect_interface" => true,
    "rules" => sing_rules,
    "rule_set" => [
      {
        "tag" => "geosite-cn",
        "type" => "remote",
        "format" => "binary",
        "url" => upstreams.fetch("sing_box").fetch("cn_domains"),
        "download_detour" => sing_proxy,
        "update_interval" => policy.fetch("update_interval")
      },
      {
        "tag" => "geoip-cn",
        "type" => "remote",
        "format" => "binary",
        "url" => upstreams.fetch("sing_box").fetch("cn_ips"),
        "download_detour" => sing_proxy,
        "update_interval" => policy.fetch("update_interval")
      }
    ],
    "final" => sing_proxy
  }
}

xray_rules = []
if proxy_server_ip
  xray_rules << { "ip" => [proxy_server_cidr], "outboundTag" => "direct", "enabled" => true, "remarks" => "Proxy server bypass" }
else
  xray_rules << { "domain" => ["full:#{proxy_server}"], "outboundTag" => "direct", "enabled" => true, "remarks" => "Proxy server bypass" }
end
xray_rules << { "ip" => PRIVATE_CIDRS, "outboundTag" => "direct", "enabled" => true, "remarks" => "Private and special-use networks" }
xray_rules << { "domain" => block_domains.map { |domain| "domain:#{domain}" }, "outboundTag" => "block", "enabled" => true, "remarks" => "Personal block domains" } unless block_domains.empty?
xray_rules << { "domain" => proxy_domains.map { |domain| "domain:#{domain}" }, "outboundTag" => "proxy", "enabled" => true, "remarks" => "Personal forced proxy domains" } unless proxy_domains.empty?
xray_rules << { "domain" => direct_domains.map { |domain| "domain:#{domain}" }, "outboundTag" => "direct", "enabled" => true, "remarks" => "Personal forced direct domains" } unless direct_domains.empty?
xray_rules << { "ip" => proxy_cidrs, "outboundTag" => "proxy", "enabled" => true, "remarks" => "Personal forced proxy networks" } unless proxy_cidrs.empty?
xray_rules << { "ip" => direct_cidrs, "outboundTag" => "direct", "enabled" => true, "remarks" => "Personal forced direct networks" } unless direct_cidrs.empty?
xray_rules << { "domain" => [upstreams.fetch("xray").fetch("cn_domains")], "outboundTag" => "direct", "enabled" => true, "remarks" => "Mainland China domains" }
xray_rules << { "ip" => [upstreams.fetch("xray").fetch("cn_ips")], "outboundTag" => "direct", "enabled" => true, "remarks" => "Mainland China networks" }
xray_rules << { "port" => "0-65535", "outboundTag" => "proxy", "enabled" => true, "remarks" => "Final proxy" }

mihomo_direct = options[:mihomo_direct_tag]
mihomo_proxy = options[:mihomo_proxy_tag]
mihomo_rules = []
mihomo_rules << if proxy_server_ip
  "#{proxy_server_address.ipv4? ? 'IP-CIDR' : 'IP-CIDR6'},#{proxy_server_cidr},#{mihomo_direct},no-resolve"
else
  "DOMAIN,#{proxy_server},#{mihomo_direct}"
end
PRIVATE_CIDRS.each do |cidr|
  family = IPAddr.new(cidr).ipv4? ? "IP-CIDR" : "IP-CIDR6"
  mihomo_rules << "#{family},#{cidr},#{mihomo_direct},no-resolve"
end
block_domains.each { |domain| mihomo_rules << "DOMAIN-SUFFIX,#{domain},REJECT" }
proxy_domains.each { |domain| mihomo_rules << "DOMAIN-SUFFIX,#{domain},#{mihomo_proxy}" }
direct_domains.each { |domain| mihomo_rules << "DOMAIN-SUFFIX,#{domain},#{mihomo_direct}" }
proxy_cidrs.each do |cidr|
  family = IPAddr.new(cidr).ipv4? ? "IP-CIDR" : "IP-CIDR6"
  mihomo_rules << "#{family},#{cidr},#{mihomo_proxy},no-resolve"
end
direct_cidrs.each do |cidr|
  family = IPAddr.new(cidr).ipv4? ? "IP-CIDR" : "IP-CIDR6"
  mihomo_rules << "#{family},#{cidr},#{mihomo_direct},no-resolve"
end
mihomo_rules << "RULE-SET,cn-domains,#{mihomo_direct}"
mihomo_rules << "RULE-SET,cn-ips,#{mihomo_direct},no-resolve"
mihomo_rules << "MATCH,#{mihomo_proxy}"

interval = policy.fetch("update_interval")
abort "Mihomo interval must use whole hours" unless interval.match?(/\A\d+h\z/)
interval_seconds = Integer(interval.delete_suffix("h")) * 3600
mihomo = <<~YAML
  rule-providers:
    cn-domains:
      type: http
      behavior: domain
      format: mrs
      path: ./rules/cn-domains.mrs
      url: #{yaml_quote(upstreams.fetch("mihomo").fetch("cn_domains"))}
      interval: #{interval_seconds}
      proxy: #{yaml_quote(mihomo_proxy)}
    cn-ips:
      type: http
      behavior: ipcidr
      format: mrs
      path: ./rules/cn-ips.mrs
      url: #{yaml_quote(upstreams.fetch("mihomo").fetch("cn_ips"))}
      interval: #{interval_seconds}
      proxy: #{yaml_quote(mihomo_proxy)}
  rules:
#{mihomo_rules.map { |rule| "    - #{yaml_quote(rule)}" }.join("\n")}
YAML

FileUtils.mkdir_p(options[:output], mode: 0o700)
artifacts = {
  "sing-box-route.json" => JSON.pretty_generate(sing_box) + "\n",
  "v2rayn-xray-routing.json" => JSON.pretty_generate(xray_rules) + "\n",
  "mihomo-rules.yaml" => mihomo
}
artifacts.each { |filename, content| write_protected(File.join(options[:output], filename), content) }

generated_at = if ENV["SOURCE_DATE_EPOCH"]
  Time.at(Integer(ENV.fetch("SOURCE_DATE_EPOCH"))).utc
else
  Time.now.utc
end
manifest = {
  "schema_version" => 1,
  "policy_name" => policy.fetch("name"),
  "generated_at" => generated_at.iso8601,
  "policy_sha256" => Digest::SHA256.file(options[:policy]).hexdigest,
  "proxy_server_kind" => proxy_server_ip ? "ip" : "domain",
  "output_tags" => {
    "sing_box" => { "direct" => sing_direct, "proxy" => sing_proxy },
    "mihomo" => { "direct" => mihomo_direct, "proxy" => mihomo_proxy },
    "v2rayn_xray" => { "direct" => "direct", "proxy" => "proxy", "block" => "block" }
  },
  "artifacts" => artifacts.transform_values { |content| Digest::SHA256.hexdigest(content) }
}
write_protected(File.join(options[:output], "manifest.json"), JSON.pretty_generate(manifest) + "\n")

puts "Created four protected routing artifacts in #{options[:output]}"
