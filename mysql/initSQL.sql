CREATE DATABASE IF NOT EXISTS `astrobot`;

CREATE TABLE IF NOT EXISTS `Grupos` (
   `id_grupo` varchar(30) NOT NULL,
   `nombre_grupo` varchar(30) NOT NULL,
   PRIMARY KEY (`id_grupo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE IF NOT EXISTS `Miembros` (
   `id_miembro` varchar(30) NOT NULL,
   `nombre_miembro` varchar(30) NOT NULL,
   PRIMARY KEY (`id_miembro`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `Grupos_Miembros` (
   `id_grupo` varchar(30) NOT NULL,
   `id_miembro` varchar(30) NOT NULL,
   `fecha_unido` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (`id_grupo`,`id_miembro`),
   KEY `id_miembro` (`id_miembro`),
   CONSTRAINT `grupos_miembros_ibfk_1` FOREIGN KEY (`id_grupo`) REFERENCES `Grupos` (`id_grupo`),
   CONSTRAINT `grupos_miembros_ibfk_2` FOREIGN KEY (`id_miembro`) REFERENCES `Miembros` (`id_miembro`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
