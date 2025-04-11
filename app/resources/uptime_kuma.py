from typing import Dict, List, Any, Optional
from datetime import datetime
import re


class UptimeKumaResource:
    """Base resource class for Uptime Kuma data transformations"""

    @staticmethod
    def transform(data: Dict) -> Dict:
        """Transform method to be implemented by subclasses"""
        return data

    @staticmethod
    def camel_to_snake(name: str) -> str:
        """Convert camelCase to snake_case"""
        if not name:
            return name
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def clean_value(value: Any) -> Any:
        """Replace None or empty string with dash"""
        if value is None or value == "":
            return "-"
        elif isinstance(value, dict):
            return {k: UptimeKumaResource.clean_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [UptimeKumaResource.clean_value(item) for item in value]
        return value


class MonitorResource(UptimeKumaResource):
    """Resource for transforming monitor data"""

    @staticmethod
    def transform(monitor: Dict) -> Dict:
        """Transform a monitor object"""
        if not monitor:
            return {}

        result = {}
        for key, value in monitor.items():
            snake_key = UptimeKumaResource.camel_to_snake(key)
            result[snake_key] = UptimeKumaResource.clean_value(value)

        # Convert boolean fields
        result["active"] = bool(monitor.get("active"))
        result["force_inactive"] = bool(monitor.get("forceInactive"))
        result["status"] = 1 if monitor.get("active") else 0
        result["maintenance"] = bool(monitor.get("maintenance"))

        # Ensure lists are properly initialized
        for list_field in ["children_ids", "notification_id_list", "tags", "kafka_producer_brokers"]:
            if list_field in result and not isinstance(result[list_field], list):
                result[list_field] = []

        return result


class CertificateInfoResource(UptimeKumaResource):
    """Resource for transforming certificate information"""

    @staticmethod
    def transform(cert_info: Dict) -> Dict:
        """Transform certificate information"""
        if not cert_info:
            return {}

        # Handle the nested structure in the JSON
        cert_details = cert_info.get("certInfo", {})

        result = {
            "valid": UptimeKumaResource.clean_value(cert_info.get("valid")),
            "subject_cn": UptimeKumaResource.clean_value(cert_details.get("subject", {}).get("CN")),
            "subject_c": UptimeKumaResource.clean_value(cert_details.get("subject", {}).get("C")),
            "subject_st": UptimeKumaResource.clean_value(cert_details.get("subject", {}).get("ST")),
            "subject_l": UptimeKumaResource.clean_value(cert_details.get("subject", {}).get("L")),
            "subject_o": UptimeKumaResource.clean_value(cert_details.get("subject", {}).get("O")),
            "issuer_cn": UptimeKumaResource.clean_value(cert_details.get("issuer", {}).get("CN")),
            "issuer_c": UptimeKumaResource.clean_value(cert_details.get("issuer", {}).get("C")),
            "issuer_o": UptimeKumaResource.clean_value(cert_details.get("issuer", {}).get("O")),
            "subject_alt_name": UptimeKumaResource.clean_value(cert_details.get("subjectaltname")),
            "info_access": UptimeKumaResource.clean_value(cert_details.get("infoAccess")),
            "valid_from": UptimeKumaResource.clean_value(cert_info.get("valid_from")),
            "valid_to": UptimeKumaResource.clean_value(cert_info.get("valid_to")),
            "days_remaining": UptimeKumaResource.clean_value(cert_info.get("days_remaining")),
            "fingerprint": UptimeKumaResource.clean_value(cert_details.get("fingerprint")),
            "serial_number": UptimeKumaResource.clean_value(cert_details.get("serialNumber")),
            "signature_algorithm": UptimeKumaResource.clean_value(cert_details.get("signatureAlgorithm"))
        }

        # Add certificate expiry status
        if result["days_remaining"] != "-" and isinstance(result["days_remaining"], (int, float)):
            if result["days_remaining"] <= 0:
                result["expiry_status"] = "expired"
            elif result["days_remaining"] <= 7:
                result["expiry_status"] = "critical"
            elif result["days_remaining"] <= 30:
                result["expiry_status"] = "warning"
            else:
                result["expiry_status"] = "ok"
        else:
            result["expiry_status"] = "-"

        return result


class HeartbeatResource(UptimeKumaResource):
    """Resource for transforming heartbeat information"""

    @staticmethod
    def transform(heartbeat: Dict) -> Dict:
        """Transform heartbeat information"""
        if not heartbeat:
            return {}

        # Handle both monitor_id and monitorID fields
        monitor_id = heartbeat.get("monitor_id", heartbeat.get("monitorID"))

        result = {
            "id": UptimeKumaResource.clean_value(heartbeat.get("id")),
            "monitor_id": UptimeKumaResource.clean_value(monitor_id),
            "status": UptimeKumaResource.clean_value(heartbeat.get("status")),
            "time": UptimeKumaResource.clean_value(heartbeat.get("time")),
            "msg": UptimeKumaResource.clean_value(heartbeat.get("msg")),
            "ping": UptimeKumaResource.clean_value(heartbeat.get("ping")),
            "duration": UptimeKumaResource.clean_value(heartbeat.get("duration")),
            "important": bool(heartbeat.get("important", False)),
            "down_count": UptimeKumaResource.clean_value(heartbeat.get("down_count", 0))
        }

        # Add ping quality indicator
        if result["ping"] != "-" and isinstance(result["ping"], (int, float)):
            if result["ping"] < 100:
                result["ping_quality"] = "excellent"
            elif result["ping"] < 300:
                result["ping_quality"] = "good"
            elif result["ping"] < 600:
                result["ping_quality"] = "fair"
            else:
                result["ping_quality"] = "poor"
        else:
            result["ping_quality"] = "-"

        return result


class UptimeKumaInfoResource(UptimeKumaResource):
    """Resource for transforming Uptime Kuma instance information"""

    @staticmethod
    def transform(info: Dict) -> Dict:
        """Transform Uptime Kuma instance information"""
        if not info:
            return {}

        result = {}
        for key, value in info.items():
            snake_key = UptimeKumaResource.camel_to_snake(key)
            result[snake_key] = UptimeKumaResource.clean_value(value)

        # Add memory usage percentage if available
        if "mem_total" in result and "mem_used" in result:
            if result["mem_total"] != "-" and result["mem_used"] != "-":
                try:
                    result["memory_usage_percent"] = round(
                        (result["mem_used"] / result["mem_total"]) * 100, 2)
                except (TypeError, ZeroDivisionError):
                    result["memory_usage_percent"] = "-"
            else:
                result["memory_usage_percent"] = "-"

        return result


class UptimeResource(UptimeKumaResource):
    """Resource for transforming uptime data"""

    @staticmethod
    def transform(uptime: Dict) -> Dict:
        """Transform uptime data"""
        if not uptime:
            return {}

        result = {}
        # Handle the uptime periods (24, 720, etc.)
        for period, value in uptime.items():
            clean_value = UptimeKumaResource.clean_value(value)
            result[f"{period}h"] = clean_value

            if clean_value != "-":
                result[f"{period}h_percent"] = round(value * 100, 2)
            else:
                result[f"{period}h_percent"] = "-"

        # Add uptime quality indicators
        for period in uptime.keys():
            percent_key = f"{period}h_percent"
            if percent_key in result and result[percent_key] != "-":
                if result[percent_key] >= 99.9:
                    result[f"{period}h_quality"] = "excellent"
                elif result[percent_key] >= 99.0:
                    result[f"{period}h_quality"] = "good"
                elif result[percent_key] >= 95.0:
                    result[f"{period}h_quality"] = "fair"
                else:
                    result[f"{period}h_quality"] = "poor"
            else:
                result[f"{period}h_quality"] = "-"

        return result


class MonitorStatisticsResource(UptimeKumaResource):
    """Resource for transforming monitor statistics"""

    @staticmethod
    def transform(data: Dict) -> Dict:
        """Transform monitor statistics"""
        if not data:
            return {}

        monitor = data.get("monitor", {})
        heartbeats = data.get("heartbeats", [])
        important_heartbeats = data.get("important_heartbeats", [])

        # Transform the first few heartbeats for preview
        recent_heartbeats = []
        for hb in heartbeats[:10]:  # Limit to 10 recent heartbeats
            recent_heartbeats.append(HeartbeatResource.transform(hb))

        # Transform important heartbeats
        transformed_important_heartbeats = []
        # Limit to 25 recent important_heartbeats
        for hb in important_heartbeats[:25]:
            transformed_important_heartbeats.append(
                HeartbeatResource.transform(hb))

        # Calculate average ping from both heartbeats and important heartbeats
        all_heartbeats = heartbeats + important_heartbeats
        valid_pings = [hb.get("ping")
                       for hb in all_heartbeats if hb.get("ping") is not None]
        avg_ping_calculated = sum(valid_pings) / \
            len(valid_pings) if valid_pings else None

        # Get uptime percentages
        uptime_data = UptimeResource.transform(data.get("uptime", {}))

        # Calculate status change frequency
        status_changes = 0
        if len(heartbeats) > 1:
            for i in range(1, len(heartbeats)):
                if heartbeats[i].get("status") != heartbeats[i-1].get("status"):
                    status_changes += 1

        # Calculate time since last status change
        last_status_change_time = None
        for hb in heartbeats:
            if hb.get("important", False):
                last_status_change_time = hb.get("time")
                break

        # Calculate response time stability (standard deviation of ping)
        ping_stability = "-"
        if valid_pings and len(valid_pings) > 1:
            try:
                import statistics
                ping_stability = round(statistics.stdev(valid_pings), 2)
            except (ImportError, statistics.StatisticsError):
                pass

        # Create logs from heartbeats
        # Combine all heartbeats
        combined_heartbeats = heartbeats + important_heartbeats

        # Sort by time if available
        if combined_heartbeats:
            try:
                # Convert time strings to datetime objects for proper sorting
                # Sort from latest to oldest
                combined_heartbeats.sort(
                    key=lambda x: datetime.fromisoformat(x.get("time")) if x.get(
                        "time") and x.get("time") != "-" else datetime.min,
                    reverse=True
                )
            except Exception:
                # Fallback to string comparison if datetime conversion fails
                combined_heartbeats.sort(
                    key=lambda x: x.get("time", ""), reverse=True)

        # Format each heartbeat as an object with properties instead of a single string
        log_entries = []
        monitor_name = monitor.get("name", "Unknown")

        for hb in combined_heartbeats:
            status = "UP" if hb.get("status") == 1 else "DOWN"
            time_str = hb.get("time", "-")
            message = hb.get("msg", "-")

            # Create a structured log entry object
            log_entry = {
                "name": monitor_name,
                "status": status,
                "time": time_str,
                "message": message
            }
            log_entries.append(log_entry)

        result = {
            "id": UptimeKumaResource.clean_value(monitor.get("id")),
            "name": UptimeKumaResource.clean_value(monitor.get("name")),
            "url": UptimeKumaResource.clean_value(monitor.get("url")),
            "type": UptimeKumaResource.clean_value(monitor.get("type")),
            "description": UptimeKumaResource.clean_value(monitor.get("description")),
            "method": UptimeKumaResource.clean_value(monitor.get("method")),
            "status": 1 if monitor.get("active") else 0,
            "active": bool(monitor.get("active")),
            "maintenance": bool(monitor.get("maintenance")),
            "interval": UptimeKumaResource.clean_value(monitor.get("interval")),
            "timeout": UptimeKumaResource.clean_value(monitor.get("timeout")),
            "avg_ping": UptimeKumaResource.clean_value(data.get("avg_ping")),
            "avg_ping_calculated": UptimeKumaResource.clean_value(avg_ping_calculated),
            "uptime": uptime_data,
            "cert_info": CertificateInfoResource.transform(data.get("cert_info", {})),
            "recent_heartbeats": recent_heartbeats,
            "heartbeats_count": len(heartbeats),
            "important_heartbeats": transformed_important_heartbeats,
            "important_heartbeats_count": len(important_heartbeats),
            "tags": UptimeKumaResource.clean_value(monitor.get("tags", [])),
            "notification_ids": UptimeKumaResource.clean_value(monitor.get("notificationIDList", [])),
            "weight": UptimeKumaResource.clean_value(monitor.get("weight")),
            "accepted_statuscodes": UptimeKumaResource.clean_value(monitor.get("accepted_statuscodes", [])),
            "maxredirects": UptimeKumaResource.clean_value(monitor.get("maxredirects")),
            "dns_resolve_type": UptimeKumaResource.clean_value(monitor.get("dns_resolve_type")),
            "dns_resolve_server": UptimeKumaResource.clean_value(monitor.get("dns_resolve_server")),
            # Additional analytics
            "status_changes_count": status_changes,
            "last_status_change": UptimeKumaResource.clean_value(last_status_change_time),
            "ping_stability": ping_stability,
            "logs": log_entries  # Add the logs field
        }

        # Add ping quality indicator
        if result["avg_ping_calculated"] != "-" and isinstance(result["avg_ping_calculated"], (int, float)):
            if result["avg_ping_calculated"] < 100:
                result["ping_quality"] = "excellent"
            elif result["avg_ping_calculated"] < 300:
                result["ping_quality"] = "good"
            elif result["avg_ping_calculated"] < 600:
                result["ping_quality"] = "fair"
            else:
                result["ping_quality"] = "poor"
        else:
            result["ping_quality"] = "-"

        # Add health score (weighted combination of uptime and ping quality)
        health_score = "-"
        if uptime_data.get("24h_percent", "-") != "-" and result["avg_ping_calculated"] != "-":
            try:
                # 70% weight to uptime
                uptime_score = uptime_data["24h_percent"] * 0.7

                # Convert ping to a 0-100 scale (lower is better)
                ping_value = result["avg_ping_calculated"]
                ping_score = max(0, 100 - (ping_value / 10)) * \
                    0.3  # 30% weight to ping

                health_score = round(uptime_score + ping_score, 1)
            except (TypeError, ValueError):
                pass

        result["health_score"] = health_score

        return result


class AllMonitorsStatisticsResource(UptimeKumaResource):
    """Resource for transforming all monitors statistics"""

    @staticmethod
    def transform(data: Dict) -> Dict:
        """Transform all monitors statistics"""
        if not data:
            return {}

        monitors = []
        for monitor_id, monitor_data in data.get("monitors", {}).items():
            monitor_stats = MonitorStatisticsResource.transform(monitor_data)
            monitor_stats["id"] = int(monitor_id)  # Ensure ID is an integer
            monitors.append(monitor_stats)

        # Sort monitors by name
        monitors.sort(key=lambda x: x.get("name", "").lower())

        # Group monitors by status with simplified data structure and additional analytics
        up_monitors = [{
            "id": m.get("id"),
            "name": m.get("name"),
            "url": m.get("url"),
            "status": m.get("status"),
            "active": m.get("active"),
            "type": m.get("type"),
            "avg_ping": m.get("avg_ping_calculated"),
            "ping_quality": m.get("ping_quality"),
            "uptime_24h": m.get("uptime", {}).get("24h_percent"),
            "health_score": m.get("health_score")
        } for m in monitors if m.get("status") == 1 and not m.get("maintenance")]

        down_monitors = [{
            "id": m.get("id"),
            "name": m.get("name"),
            "url": m.get("url"),
            "status": m.get("status"),
            "active": m.get("active"),
            "type": m.get("type"),
            "last_error": m.get("important_heartbeats")[0].get("msg") if m.get("important_heartbeats") else "-",
            "down_since": m.get("important_heartbeats")[0].get("time") if m.get("important_heartbeats") else "-"
        } for m in monitors if m.get("status") == 0 and not m.get("maintenance")]

        maintenance_monitors = [{
            "id": m.get("id"),
            "name": m.get("name"),
            "url": m.get("url"),
            "status": m.get("status"),
            "active": m.get("active"),
            "type": m.get("type")
        } for m in monitors if m.get("maintenance")]

        # Add timestamp
        current_time = datetime.now().isoformat()

        # Calculate average health score across all monitors
        health_scores = [m.get("health_score") for m in monitors
                         if m.get("health_score") != "-" and not m.get("maintenance")]
        avg_health_score = "-"
        if health_scores:
            try:
                avg_health_score = round(
                    sum(health_scores) / len(health_scores), 1)
            except (TypeError, ZeroDivisionError):
                pass

        return {
            "uptime_kuma_info": UptimeKumaInfoResource.transform(data.get("uptime_kuma_info", {})),
            "monitors": monitors,
            "monitors_count": len(monitors),
            "up_monitors": up_monitors,
            "down_monitors": down_monitors,
            "maintenance_monitors": maintenance_monitors,
            "up_monitors_count": len(up_monitors),
            "down_monitors_count": len(down_monitors),
            "maintenance_monitors_count": len(maintenance_monitors),
            "up_percentage": round(len(up_monitors) / (len(up_monitors) + len(down_monitors)) * 100, 2) if (len(up_monitors) + len(down_monitors)) > 0 else 0,
            "timestamp": current_time,
            "avg_health_score": avg_health_score,
            # Additional analytics
            "monitor_types": list(set(m.get("type") for m in monitors if m.get("type") != "-")),
            "monitors_by_type": {t: len([m for m in monitors if m.get("type") == t])
                                 for t in set(m.get("type") for m in monitors if m.get("type") != "-")},
            "avg_response_time": round(sum(m.get("avg_ping_calculated") for m in monitors
                                           if m.get("avg_ping_calculated") != "-" and not m.get("maintenance")) /
                                       len([m for m in monitors if m.get("avg_ping_calculated") != "-" and not m.get("maintenance")]), 2)
            if len([m for m in monitors if m.get("avg_ping_calculated") != "-" and not m.get("maintenance")]) > 0 else "-"
        }
