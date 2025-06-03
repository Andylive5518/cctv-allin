<?php
// Zabbix GUI configuration file.
// ഇത് സാധാരണയായി Docker കണ്ടെയ്നർ ആരംഭിക്കുമ്പോൾ എൻവയോൺമെന്റ് വേരിയബിളുകളിൽ നിന്ന് സൃഷ്ടിക്കപ്പെടുന്നു.
// This file is usually generated from environment variables when the Docker container starts.

global $DB; // Zabbix数据库连接信息

// 从环境变量获取数据库连接信息 (由Docker镜像处理)
// $DB['TYPE']     = getenv('DB_TYPE') ?: 'MYSQL';
// $DB['SERVER']   = getenv('DB_SERVER_HOST') ?: 'mysql';
// $DB['PORT']     = getenv('DB_SERVER_PORT') ?: '3306';
// $DB['DATABASE'] = getenv('MYSQL_DATABASE') ?: 'zabbix';
// $DB['USER']     = getenv('MYSQL_USER') ?: 'zabbix';
// $DB['PASSWORD'] = getenv('MYSQL_PASSWORD') ?: 'zabbixpassword';

// Zabbix服务器信息
// $ZBX_SERVER      = getenv('ZBX_SERVER_HOST') ?: 'zabbix-server';
// $ZBX_SERVER_PORT = getenv('ZBX_SERVER_PORT') ?: '10051';
// $ZBX_SERVER_NAME = getenv('ZBX_SERVER_NAME') ?: ''; // 可选，在UI中显示的Zabbix服务器名称

// 其他UI设置
// $IMAGE_FORMAT_DEFAULT = IMAGE_FORMAT_PNG; // 默认图像格式
// $PHP_TZ = getenv('PHP_TZ') ?: 'Asia/Shanghai'; // PHP时区，已在docker-compose中设置

// 如果需要自定义这些值并且它们没有被环境变量覆盖，可以在这里设置。
// 但是，推荐通过docker-compose.yml中的环境变量来配置，以保持灵活性。

// 示例：如果直接提供值 (不推荐用于生产环境，除非特定场景)
/*
$DB['TYPE']     = 'MYSQL';
$DB['SERVER']   = 'mysql';
$DB['PORT']     = '3306';
$DB['DATABASE'] = 'zabbix';
$DB['USER']     = 'zabbix_user_from_conf'; // 仅为示例
$DB['PASSWORD'] = 'zabbix_pass_from_conf'; // 仅为示例

$ZBX_SERVER      = 'zabbix-server';
$ZBX_SERVER_PORT = '10051';
*/

// 这个文件主要是为了让挂载的卷不为空，实际配置由容器启动脚本根据环境变量生成。
// 如果Zabbix Web容器启动时发现此文件已存在且内容有效，它可能会使用此文件。
// 确保此路径在docker-compose.yml中正确映射到Zabbix Web容器的配置目录。

echo "<?php\n"; // 确保它是一个有效的PHP文件，即使内容大部分是注释。
?>