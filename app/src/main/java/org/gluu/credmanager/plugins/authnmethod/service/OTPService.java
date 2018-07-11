/*
 * cred-manager is available under the MIT License (2008). See http://opensource.org/licenses/MIT for full text.
 *
 * Copyright (c) 2018, Gluu
 */
package org.gluu.credmanager.plugins.authnmethod.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.lochbridge.oath.otp.keyprovisioning.OTPKey;
import org.gluu.credmanager.core.ldap.PersonOTP;
import org.gluu.credmanager.core.pojo.OTPDevice;
import org.gluu.credmanager.misc.Utils;
import org.gluu.credmanager.plugins.authnmethod.OTPExtension;
import org.gluu.credmanager.plugins.authnmethod.conf.OTPConfig;
import org.gluu.credmanager.plugins.authnmethod.conf.otp.HOTPConfig;
import org.gluu.credmanager.plugins.authnmethod.conf.otp.TOTPConfig;
import org.gluu.credmanager.plugins.authnmethod.service.otp.HOTPAlgorithmService;
import org.gluu.credmanager.plugins.authnmethod.service.otp.IOTPAlgorithm;
import org.gluu.credmanager.plugins.authnmethod.service.otp.TOTPAlgorithmService;
import org.slf4j.Logger;

import javax.annotation.PostConstruct;
import javax.enterprise.context.ApplicationScoped;
import javax.inject.Inject;
import javax.inject.Named;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * @author jgomer
 */
@Named
@ApplicationScoped
public class OTPService extends BaseService {

    @Inject
    private Logger logger;

    @Inject
    private TOTPAlgorithmService tAS;

    @Inject
    private HOTPAlgorithmService hAS;

    private OTPConfig conf;

    @PostConstruct
    private void inited() {
        reloadConfiguration();
    }

    public OTPConfig getConf() {
        return conf;
    }

    public void reloadConfiguration() {

        String acr = OTPExtension.ACR;
        Map<String, String> props = ldapService.getCustScriptConfigProperties(acr);
        if (props == null) {
            logger.warn("Config. properties for custom script '{}' could not be read. Features related to {} will not be accessible",
                    acr, acr.toUpperCase());
        } else {
            conf = OTPConfig.get(props);
        }

    }

    public int getDevicesTotal(String userId) {

        int total = 0;
        try {
            PersonOTP person = ldapService.get(PersonOTP.class, ldapService.getPersonDn(userId));
            total = (int) person.getExternalUids().stream().filter(uid -> uid.startsWith("totp:") || uid.startsWith("hotp:")).count();
        } catch (Exception e) {
            logger.error(e.getMessage(), e);
        }
        return total;

    }

    public List<OTPDevice> getDevices(String userId) {

        List<OTPDevice> devices = new ArrayList<>();
        try {
            PersonOTP person = ldapService.get(PersonOTP.class, ldapService.getPersonDn(userId));
            String json = person.getOTPDevices();
            json = Utils.isEmpty(json) ? "[]" : mapper.readTree(json).get("devices").toString();

            List<OTPDevice> devs = mapper.readValue(json, new TypeReference<List<OTPDevice>>() { });
            devices = person.getExternalUids().stream().filter(uid -> uid.startsWith("totp:") || uid.startsWith("hotp:"))
                    .map(uid -> getExtraOTPInfo(uid, devs)).sorted().collect(Collectors.toList());
            logger.trace("getDevices. User '{}' has {}", userId, devices.stream().map(OTPDevice::getId).collect(Collectors.toList()));
        } catch (Exception e) {
            logger.error(e.getMessage(), e);
        }
        return devices;

    }

    public boolean updateDevicesAdd(String userId, List<OTPDevice> devices, OTPDevice newDevice) {

        boolean success = false;
        try {
            List<OTPDevice> vdevices = new ArrayList<>(devices);
            if (newDevice != null) {
                vdevices.add(newDevice);
            }
            String[] uids = vdevices.stream().map(OTPDevice::getUid).toArray(String[]::new);
            String json = uids.length == 0 ? null : mapper.writeValueAsString(Collections.singletonMap("devices", vdevices));

            logger.debug("Updating otp devices for user '{}'", userId);
            PersonOTP person = ldapService.get(PersonOTP.class, ldapService.getPersonDn(userId));
            person.setOTPDevices(json);
            person.setExternalUid(uids);

            success = ldapService.modify(person, PersonOTP.class);

            if (success && newDevice != null) {
                devices.add(newDevice);
                logger.debug("Added {}", newDevice.getNickName());
            }
        } catch (Exception e) {
            logger.error(e.getMessage(), e);
        }
        return success;

    }

    public boolean addDevice(String userId, OTPDevice newDevice) {
        return updateDevicesAdd(userId, getDevices(userId), newDevice);
    }

    /**
     * Creates an instance of OTPDevice by looking up in the list of OTPDevices passed. If the item is not found in the
     * in the list, it means the device was previously enrolled by using a different application. In this case the resulting
     * object will not have properties like nickname, etc. Just a basic ID
     * @param uid Identifier of an OTP device (LDAP attribute "oxExternalUid" inside a user entry)
     * @param list List of existing OTP devices enrolled. Ideally, there is an item here corresponding to the uid passed
     * @return OTPDevice object
     */
    private OTPDevice getExtraOTPInfo(String uid, List<OTPDevice> list) {
        //Complements current otp device with extra info in the list if any

        OTPDevice device = new OTPDevice(uid);
        int hash = device.getId();

        Optional<OTPDevice> extraInfoOTP = list.stream().filter(dev -> dev.getId() == hash).findFirst();
        if (extraInfoOTP.isPresent()) {
            device.setAddedOn(extraInfoOTP.get().getAddedOn());
            device.setNickName(extraInfoOTP.get().getNickName());
        }
        return device;

    }

    public IOTPAlgorithm getAlgorithmService(OTPKey.OTPType type) {

        switch (type) {
            case HOTP:
                hAS.init((HOTPConfig) Utils.cloneObject(conf.getHotp()), conf.getIssuer());
                return hAS;
            case TOTP:
                tAS.init((TOTPConfig) Utils.cloneObject(conf.getTotp()), conf.getIssuer());
                return tAS;
            default:
                return null;
        }
    }

}
